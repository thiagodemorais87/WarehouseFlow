"""Testes de login, JWT e permissões por perfil (ADMIN / GESTOR / OPERADOR).

Rodam sem Docker: usam um SQLite em memória no lugar do PostgreSQL.
"""

from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app
from app.security import ALGORITHM, SECRET_KEY, create_access_token, hash_password


# ---------------------------------------------------------------------------
# Banco de testes (SQLite em memória, uma única conexão compartilhada)
# ---------------------------------------------------------------------------

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


# Senhas de teste. O hash é gerado uma vez só, porque o bcrypt é lento de propósito.
PASSWORDS = {"admin": "admin123", "gestor": "gestor123", "operador": "operador123"}
HASHES = {who: hash_password(senha) for who, senha in PASSWORDS.items()}
ROLE_NAMES = {"admin": "ADMIN", "gestor": "GESTOR", "operador": "OPERADOR"}

# Preenchido pelo seed(): guarda os ids criados em cada teste
IDS: dict = {}


def seed():
    """Cria perfis, 3 usuários (um por perfil), 1 pedido e 2 tarefas."""
    db = TestingSession()

    roles = {name: models.Role(name=name) for name in ROLE_NAMES.values()}
    db.add_all(roles.values())
    db.flush()

    users = {}
    for who, role_name in ROLE_NAMES.items():
        user = models.User(
            name=who.title(),
            email=f"{who}@teste.com",
            password_hash=HASHES[who],
            role_id=roles[role_name].id,
        )
        db.add(user)
        users[who] = user
    db.flush()

    order = models.Order(type="OUTBOUND", status="PENDING")
    db.add(order)
    db.flush()

    task_operador = models.Task(
        type="PICKING", status="PENDING", order_id=order.id,
        assigned_user_id=users["operador"].id,
    )
    task_admin = models.Task(
        type="PICKING", status="PENDING", order_id=order.id,
        assigned_user_id=users["admin"].id,
    )
    db.add_all([task_operador, task_admin])
    db.commit()

    IDS.clear()
    IDS.update(
        {who: user.id for who, user in users.items()},
        role_operador=roles["OPERADOR"].id,
        task_operador=task_operador.id,
        task_admin=task_admin.id,
    )
    db.close()


@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    seed()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Ajudantes
# ---------------------------------------------------------------------------

def login(client, who, password=None):
    return client.post(
        "/auth/login",
        data={"username": f"{who}@teste.com", "password": password or PASSWORDS[who]},
    )


def auth(client, who):
    """Faz login e devolve o cabeçalho Authorization pronto para usar."""
    token = login(client, who).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Login e token
# ---------------------------------------------------------------------------

def test_login_correto_devolve_token(client):
    resp = login(client, "admin")
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"

    payload = jwt.decode(body["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == str(IDS["admin"])
    assert payload["role"] == "ADMIN"


def test_login_senha_errada_devolve_401(client):
    assert login(client, "admin", "senha-errada").status_code == 401


def test_login_email_inexistente_devolve_401(client):
    resp = client.post("/auth/login", data={"username": "ninguem@teste.com", "password": "x12345"})
    assert resp.status_code == 401


def test_me_devolve_usuario_logado(client):
    resp = client.get("/auth/me", headers=auth(client, "gestor"))
    assert resp.status_code == 200
    assert resp.json()["email"] == "gestor@teste.com"


def test_token_invalido_devolve_401(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer token-falso"})
    assert resp.status_code == 401


def test_token_expirado_devolve_401(client):
    expirado = create_access_token(
        {"sub": str(IDS["admin"]), "role": "ADMIN"}, expires_delta=timedelta(minutes=-1)
    )
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {expirado}"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /users: só ADMIN
# ---------------------------------------------------------------------------

def test_users_sem_token_devolve_401(client):
    assert client.get("/users/").status_code == 401


def test_users_operador_devolve_403(client):
    assert client.get("/users/", headers=auth(client, "operador")).status_code == 403


def test_users_gestor_devolve_403(client):
    assert client.get("/users/", headers=auth(client, "gestor")).status_code == 403


def test_users_admin_lista_sem_expor_senha(client):
    resp = client.get("/users/", headers=auth(client, "admin"))
    assert resp.status_code == 200
    usuarios = resp.json()
    assert len(usuarios) == 3
    for usuario in usuarios:
        assert "password" not in usuario
        assert "password_hash" not in usuario


def test_admin_cria_usuario_com_senha_hasheada_e_ele_consegue_logar(client):
    novo = {
        "name": "Novo Operador",
        "email": "novo@teste.com",
        "password": "senha123",
        "role_id": IDS["role_operador"],
    }
    resp = client.post("/users/", json=novo, headers=auth(client, "admin"))
    assert resp.status_code == 201

    # A senha não pode estar guardada em texto puro
    db = TestingSession()
    salvo = db.query(models.User).filter(models.User.email == "novo@teste.com").first()
    assert salvo.password_hash != "senha123"
    db.close()

    # E o novo usuário consegue entrar com ela
    resp = client.post("/auth/login", data={"username": "novo@teste.com", "password": "senha123"})
    assert resp.status_code == 200


def test_email_duplicado_devolve_400(client):
    duplicado = {"name": "Outro", "email": "admin@teste.com", "password": "senha123"}
    resp = client.post("/users/", json=duplicado, headers=auth(client, "admin"))
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Produtos: logado vê, ADMIN/GESTOR altera
# ---------------------------------------------------------------------------

PRODUTO = {"sku": "T-001", "name": "Produto de teste"}


def test_produtos_sem_token_devolve_401(client):
    assert client.get("/products/").status_code == 401


def test_operador_pode_listar_produtos(client):
    assert client.get("/products/", headers=auth(client, "operador")).status_code == 200


def test_operador_nao_cria_produto(client):
    resp = client.post("/products/", json=PRODUTO, headers=auth(client, "operador"))
    assert resp.status_code == 403


def test_gestor_cria_produto(client):
    resp = client.post("/products/", json=PRODUTO, headers=auth(client, "gestor"))
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Tarefas: operador só vê e altera as próprias
# ---------------------------------------------------------------------------

def test_admin_ve_todas_as_tarefas(client):
    resp = client.get("/tasks/", headers=auth(client, "admin"))
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_operador_ve_so_as_proprias_tarefas(client):
    resp = client.get("/tasks/", headers=auth(client, "operador"))
    assert resp.status_code == 200
    atribuidos = [t["assigned_user_id"] for t in resp.json()]
    assert atribuidos == [IDS["operador"]]


def test_operador_nao_abre_tarefa_de_outro(client):
    resp = client.get(f"/tasks/{IDS['task_admin']}", headers=auth(client, "operador"))
    assert resp.status_code == 403


def test_operador_atualiza_status_da_propria_tarefa(client):
    resp = client.put(
        f"/tasks/{IDS['task_operador']}",
        json={"status": "IN_PROGRESS"},
        headers=auth(client, "operador"),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"


def test_operador_nao_altera_tarefa_de_outro(client):
    resp = client.put(
        f"/tasks/{IDS['task_admin']}",
        json={"status": "COMPLETED"},
        headers=auth(client, "operador"),
    )
    assert resp.status_code == 403


def test_operador_nao_reatribui_tarefa(client):
    resp = client.put(
        f"/tasks/{IDS['task_operador']}",
        json={"assigned_user_id": IDS["admin"]},
        headers=auth(client, "operador"),
    )
    assert resp.status_code == 403


def test_operador_nao_cria_tarefa(client):
    nova = {"type": "PICKING", "order_id": 1}
    resp = client.post("/tasks/", json=nova, headers=auth(client, "operador"))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Tela de login (cookie, página inicial e logout)
# ---------------------------------------------------------------------------

def entrar_pela_tela(client, who):
    """Envia o formulário de login. O cookie fica guardado no próprio client."""
    return client.post(
        "/login",
        data={"email": f"{who}@teste.com", "password": PASSWORDS[who]},
        follow_redirects=False,
    )


def test_pagina_de_login_carrega(client):
    assert client.get("/login").status_code == 200


def test_login_pela_tela_redireciona_e_grava_cookie(client):
    resp = entrar_pela_tela(client, "admin")
    assert resp.status_code == 303
    assert resp.headers["location"] == "/inicio"
    assert "access_token=" in resp.headers["set-cookie"]


def test_login_pela_tela_com_senha_errada_mostra_erro(client):
    resp = client.post(
        "/login",
        data={"email": "admin@teste.com", "password": "errada"},
        follow_redirects=False,
    )
    assert resp.status_code == 401
    assert "E-mail ou senha incorretos" in resp.text
    assert "access_token" not in resp.headers.get("set-cookie", "")


def test_inicio_sem_login_volta_para_o_login(client):
    resp = client.get("/inicio", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"


def test_menu_do_operador_nao_mostra_usuarios(client):
    entrar_pela_tela(client, "operador")
    resp = client.get("/inicio")
    assert resp.status_code == 200
    assert "Olá, Operador" in resp.text
    assert "/users/" not in resp.text
    assert "/locations/" not in resp.text


def test_menu_do_admin_mostra_usuarios(client):
    entrar_pela_tela(client, "admin")
    resp = client.get("/inicio")
    assert resp.status_code == 200
    assert "/users/" in resp.text


def test_api_aceita_o_cookie_depois_do_login(client):
    entrar_pela_tela(client, "admin")
    assert client.get("/users/").status_code == 200


def test_logout_apaga_o_cookie(client):
    entrar_pela_tela(client, "admin")
    resp = client.post("/logout", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"
    assert client.get("/inicio", follow_redirects=False).status_code == 303