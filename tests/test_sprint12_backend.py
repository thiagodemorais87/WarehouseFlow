"""Sprint 12 — fechamento do backend (health, Swagger, persistência, seed).

Parte SQLite: sempre roda.
Parte PostgreSQL: requer TEST_DATABASE_URL (banco de TESTE — o schema public é recriado).
"""

import os
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "backend/database/schema.sql").read_text(encoding="utf-8")
SEED = (ROOT / "backend/database/seed.sql").read_text(encoding="utf-8")
MIG_003 = (ROOT / "backend/database/migrations/003_volume_precisao.sql").read_text(encoding="utf-8")
PG_URL = os.getenv("TEST_DATABASE_URL", "")


# Seed


def test_seed_volumes_cabem_na_coluna():
    """Nenhum volume do seed pode ter mais casas que a coluna (senão vira 0.00)."""
    escala = int(re.search(r"volume DECIMAL\(10,(\d)\)", SCHEMA).group(1))
    bloco = SEED.split("INSERT INTO products")[1].split("ON CONFLICT")[0]
    volumes = re.findall(r",\s*([0-9.]+)\)", bloco)
    assert volumes, "seed sem produtos?"
    for v in volumes:
        casas = len(v.split(".")[1]) if "." in v else 0
        assert casas <= escala, f"volume {v} excede {escala} casas"


# Health


def test_health_confere_o_banco():
    with TestClient(app) as client:
        r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["database"] == "ok"
    assert "version" in r.json()


def test_health_retorna_503_com_banco_fora():
    class SessaoQuebrada:
        def execute(self, *_a, **_k):
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

        def close(self):
            pass

    app.dependency_overrides[get_db] = lambda: SessaoQuebrada()
    try:
        with TestClient(app) as client:
            r = client.get("/health")
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert r.status_code == 503
    assert r.json()["database"] == "unavailable"


def test_swagger_e_openapi_no_ar():
    with TestClient(app) as client:
        assert client.get("/docs").status_code == 200
        spec = client.get("/openapi.json").json()
    for rota in ("/products/", "/stock", "/orders/", "/tasks/", "/optimization/route/by-order", "/health"):
        assert rota in spec["paths"], rota


# PostgreSQL real


@pytest.fixture
def pg():
    if not PG_URL.startswith("postgresql"):
        pytest.skip("requer TEST_DATABASE_URL (PostgreSQL)")
    from sqlalchemy import create_engine

    engine = create_engine(PG_URL, isolation_level="AUTOCOMMIT")
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    yield engine
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    engine.dispose()


def test_seed_preserva_volume_com_4_casas(pg):
    with pg.begin() as conn:
        conn.exec_driver_sql(SCHEMA)
        conn.exec_driver_sql(SEED)
        vol = conn.exec_driver_sql("SELECT volume FROM products WHERE sku = 'PROD-004'").scalar()
    assert float(vol) == pytest.approx(0.0008)


def test_migration_003_corrige_banco_antigo_e_e_idempotente(pg):
    antigo = SCHEMA.replace("volume DECIMAL(10,4)", "volume DECIMAL(10,2)")
    with pg.begin() as conn:
        conn.exec_driver_sql(antigo)
        conn.exec_driver_sql(SEED)
        assert float(conn.exec_driver_sql("SELECT volume FROM products WHERE sku='PROD-004'").scalar()) == 0
        conn.exec_driver_sql(MIG_003)
        conn.exec_driver_sql(MIG_003)  # 2ª vez: no-op
        vol = conn.exec_driver_sql("SELECT volume FROM products WHERE sku='PROD-004'").scalar()
        escala = conn.exec_driver_sql(
            "SELECT numeric_scale FROM information_schema.columns "
            "WHERE table_name='products' AND column_name='volume'"
        ).scalar()
    assert float(vol) == pytest.approx(0.0008)
    assert escala == 4


def test_dados_persistem_apos_restart_do_pool(pg):
    """Simula o restart da API: grava, descarta o engine inteiro e lê com um engine novo."""
    from sqlalchemy import create_engine

    with pg.begin() as conn:
        conn.exec_driver_sql(SCHEMA)
        conn.exec_driver_sql(SEED)
        conn.exec_driver_sql("INSERT INTO products (sku, name, volume) VALUES ('PERSIST-1', 'Persistência', 0.0123)")
        conn.exec_driver_sql("INSERT INTO orders (type) VALUES ('OUTBOUND')")
    pg.dispose()

    novo = create_engine(PG_URL)
    try:
        with novo.connect() as conn:
            vol = conn.exec_driver_sql("SELECT volume FROM products WHERE sku='PERSIST-1'").scalar()
            pedidos = conn.exec_driver_sql("SELECT count(*) FROM orders").scalar()
    finally:
        novo.dispose()
    assert float(vol) == pytest.approx(0.0123)
    assert pedidos == 7  # 6 do seed + 1 novo (sequência ajustada pelo seed)
