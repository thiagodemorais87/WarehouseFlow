"""Infraestrutura dos testes funcionais de CRUD e de regras da API.

Diferenças em relação ao fixture `client` de test_auth.py:
- SQLite com PRAGMA foreign_keys=ON (ou PostgreSQL via TEST_DATABASE_URL), para as FKs (ON DELETE CASCADE/RESTRICT)
  se comportarem como no PostgreSQL;
- raise_server_exceptions=False: um erro interno vira resposta 500 e o teste
  falha com o status correto, em vez de estourar uma exceção no meio do teste.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app
from tests.test_auth import HASHES, PASSWORDS, ROLE_NAMES

# Por padrão roda em SQLite (sem Docker). Para validar contra o PostgreSQL real:
#   TEST_DATABASE_URL=postgresql+psycopg2://warehouse:warehouse@localhost:5433/warehouseflow_test pytest
# (use um banco de teste: as tabelas são apagadas ao fim de cada teste)
_TEST_DB_URL = os.getenv("TEST_DATABASE_URL")

if _TEST_DB_URL:
    engine = create_engine(_TEST_DB_URL)
else:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _override_get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


def _seed_users():
    db = Session()
    roles = {name: models.Role(name=name) for name in ROLE_NAMES.values()}
    db.add_all(roles.values())
    db.flush()
    for who, role_name in ROLE_NAMES.items():
        db.add(
            models.User(
                name=who.title(),
                email=f"{who}@teste.com",
                password_hash=HASHES[who],
                role_id=roles[role_name].id,
            )
        )
    db.commit()
    db.close()


class Api:
    """Cliente HTTP autenticado como ADMIN, com atalhos para os outros perfis."""

    def __init__(self, http: TestClient):
        self.http = http
        self.headers = {
            who: self._login(who) for who in ("admin", "gestor", "operador")
        }

    def _login(self, who: str) -> dict:
        resp = self.http.post(
            "/auth/login",
            json={"email": f"{who}@teste.com", "password": PASSWORDS[who]},
        )
        assert resp.status_code == 200, resp.text
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    def call(self, method: str, url: str, who: str = "admin", **kwargs):
        self.http.cookies.clear()
        return self.http.request(method, url, headers=self.headers[who], **kwargs)

    def get(self, url, **kw):
        return self.call("GET", url, **kw)

    def post(self, url, json=None, **kw):
        return self.call("POST", url, json=json, **kw)

    def put(self, url, json=None, **kw):
        return self.call("PUT", url, json=json, **kw)

    def delete(self, url, **kw):
        return self.call("DELETE", url, **kw)

    # --- criação rápida de dados de apoio (falha cedo se a API recusar) ---
    def product(self, sku="SKU-1", name="Produto", **extra) -> dict:
        resp = self.post("/products/", {"sku": sku, "name": name, **extra})
        assert resp.status_code == 201, resp.text
        return resp.json()

    def warehouse(self, name="Armazém 1") -> dict:
        resp = self.post("/locations/warehouses", {"name": name})
        assert resp.status_code == 201, resp.text
        return resp.json()

    def location(self, warehouse_id: int, code="A1-01-A", **extra) -> dict:
        resp = self.post(
            "/locations", {"warehouse_id": warehouse_id, "code": code, **extra}
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    def stock(self, product_id: int, location_id: int, quantity=10) -> dict:
        resp = self.post(
            "/stock",
            {"product_id": product_id, "location_id": location_id, "quantity": quantity},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    def order(self, items, type="OUTBOUND", **extra) -> dict:
        resp = self.post("/orders/", {"type": type, "items": items, **extra})
        assert resp.status_code == 201, resp.text
        return resp.json()

    def task(self, order_id: int, **extra) -> dict:
        resp = self.post("/tasks/", {"type": "PICKING", "order_id": order_id, **extra})
        assert resp.status_code == 201, resp.text
        return resp.json()

    def user_id(self, who: str) -> int:
        db = Session()
        try:
            return db.query(models.User).filter_by(email=f"{who}@teste.com").one().id
        finally:
            db.close()


@pytest.fixture
def api():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = _override_get_db
    _seed_users()
    http = TestClient(app, raise_server_exceptions=False)
    yield Api(http)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)