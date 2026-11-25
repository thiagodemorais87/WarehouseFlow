"""Regressão: filtros de período e perfil nos relatórios de picking.

O merge 57cf50e havia revertido o optimization_engine.py para a versão sem
filtros, deixando `date_from`, `date_to` e `role` (documentados no Api-doc.md)
sem efeito. Estes testes impedem que isso volte a acontecer.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")

from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.deps import get_current_user
from app.models import Role, User
from app.models.optimization_run import OptimizationRun
from app.routers.optimization_engine import router as optimization_router


class _Admin:
    id = 1
    email = "admin@teste.com"
    is_active = True
    role_name = "ADMIN"


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)


def _get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
app.include_router(optimization_router)
app.dependency_overrides[get_current_user] = lambda: _Admin()
app.dependency_overrides[get_db] = _get_db
client = TestClient(app)


def _run(user_id, email, quando, reducao, percentual):
    return OptimizationRun(
        user_id=user_id, user_email=email, executed_at=quando, source="route",
        original_route=["A"], nearest_neighbor_route=["A"], two_opt_route=["A"],
        distance_before=10 + reducao, nearest_neighbor_distance=10, two_opt_distance=10,
        distance_after=10, distance_reduction=reducao, reduction_percent=percentual,
        execution_time_ms=1.0, locations_count=1,
    )


def _seed():
    db = Session()
    db.add_all([Role(id=1, name="ADMIN"), Role(id=2, name="OPERADOR"), Role(id=3, name="GESTOR")])
    db.add_all([
        User(id=1, name="Admin", email="admin@teste.com", password_hash="x", role_id=1),
        User(id=2, name="Joao", email="joao@teste.com", password_hash="x", role_id=2),
        User(id=3, name="Maria", email="maria@teste.com", password_hash="x", role_id=3),
    ])
    db.add_all([
        _run(2, "joao@teste.com", datetime(2026, 10, 26, 9, 10), 10, 25),
        _run(3, "maria@teste.com", datetime(2026, 10, 27, 15, 30), 10, 20),
        _run(1, "admin@teste.com", datetime(2026, 10, 28, 9, 0), 24, 30),
    ])
    db.commit()
    db.close()


_seed()


def _ids(resp):
    assert resp.status_code == 200, resp.text
    return [r["id"] for r in resp.json()]


def test_sem_filtro_retorna_tudo_do_mais_recente_para_o_mais_antigo():
    assert _ids(client.get("/optimization/reports/picking")) == [3, 2, 1]


def test_filtro_de_perfil_restringe_pelo_usuario_que_executou():
    assert _ids(client.get("/optimization/reports/picking", params={"role": "OPERADOR"})) == [1]
    assert _ids(client.get("/optimization/reports/picking", params={"role": "GESTOR"})) == [2]
    assert _ids(client.get("/optimization/reports/picking", params={"role": "ADMIN"})) == [3]


def test_filtro_de_periodo_e_inclusivo_nas_duas_pontas():
    assert _ids(client.get("/optimization/reports/picking", params={"date_from": "2026-10-27"})) == [3, 2]
    assert _ids(client.get("/optimization/reports/picking", params={"date_to": "2026-10-27"})) == [2, 1]
    assert _ids(client.get("/optimization/reports/picking",
                           params={"date_from": "2026-10-27", "date_to": "2026-10-27"})) == [2]


def test_filtros_combinados():
    resp = client.get("/optimization/reports/picking", params={"role": "OPERADOR", "date_from": "2026-10-27"})
    assert _ids(resp) == []


def test_resumo_respeita_os_filtros():
    todos = client.get("/optimization/reports/summary").json()
    assert todos["runs_count"] == 3 and round(todos["average_distance_reduction"], 4) == round(44 / 3, 4)
    operador = client.get("/optimization/reports/summary", params={"role": "OPERADOR"}).json()
    assert operador == {"runs_count": 1, "average_distance_reduction": 10.0, "average_reduction_percent": 25.0}
    vazio = client.get("/optimization/reports/summary", params={"date_from": "2027-01-01"}).json()
    assert vazio == {"runs_count": 0, "average_distance_reduction": 0.0, "average_reduction_percent": 0.0}


def test_csv_respeita_os_filtros():
    resp = client.get("/optimization/reports/picking.csv", params={"role": "OPERADOR"})
    assert resp.status_code == 200 and "text/csv" in resp.headers["content-type"]
    linhas = resp.text.strip().splitlines()
    assert len(linhas) == 2 and "joao@teste.com" in linhas[1]


def test_periodo_invertido_retorna_400():
    resp = client.get("/optimization/reports/picking", params={"date_from": "2026-10-28", "date_to": "2026-10-01"})
    assert resp.status_code == 400