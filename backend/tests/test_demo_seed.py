"""Dados de demonstração estáveis: seed, schema e docker-compose.

Parte estática (sempre roda): protege contra regressões nos arquivos SQL/compose.
Parte PostgreSQL (só com TEST_DATABASE_URL): aplica schema.sql + seed.sql de
verdade, duas vezes, e confere que nada duplica.
"""

import os
import re
from pathlib import Path

import pytest

from app.security import verify_password

ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / "backend" / "database"
SEED = (DB_DIR / "seed.sql").read_text(encoding="utf-8")
SCHEMA = (DB_DIR / "schema.sql").read_text(encoding="utf-8")
COMPOSE = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

TABELAS = ["roles", "users", "warehouses", "locations", "products", "stock",
           "orders", "order_items", "tasks", "optimization_results"]


def _inserts():
    return re.findall(r"INSERT INTO (\w+)[^;]*?;", SEED, re.S)


def test_todo_insert_do_seed_e_idempotente():
    blocos = re.findall(r"INSERT INTO \w+.*?;", SEED, re.S)
    assert len(blocos) == len(TABELAS)
    for bloco in blocos:
        assert "ON CONFLICT" in bloco, bloco[:60]


@pytest.mark.parametrize("tabela", ["order_items", "stock", "optimization_results"])
def test_inserts_sem_chave_natural_usam_id_explicito(tabela):
    """Sem id explícito o ON CONFLICT nunca dispara e o seed duplica ao rodar de novo."""
    bloco = re.search(rf"INSERT INTO {tabela} \(([^)]*)\)", SEED).group(1)
    assert bloco.split(",")[0].strip() == "id"


@pytest.mark.parametrize("tabela", TABELAS)
def test_sequencia_de_cada_tabela_e_ajustada_apos_o_seed(tabela):
    assert f"setval('{tabela}_id_seq'" in SEED


def test_senha_de_demo_confere_com_o_hash_do_seed():
    hashes = set(re.findall(r"'(\$2b\$12\$[^']+)'", SEED))
    assert len(hashes) == 1
    assert verify_password("admin123", hashes.pop())


def test_schema_tem_checks_e_nao_aceita_fk_nula():
    for nome in ["ck_stock_quantity_non_negative", "ck_order_items_quantity_positive",
                 "ck_orders_status", "ck_tasks_status", "ck_products_weight_non_negative"]:
        assert nome in SCHEMA
    assert "ON DELETE RESTRICT" in SCHEMA


def test_healthcheck_do_postgres_usa_tcp():
    """Sem -h 127.0.0.1 o healthcheck passa durante o initdb, antes do seed terminar."""
    assert "pg_isready -h 127.0.0.1" in COMPOSE


def test_migration_e_idempotente_e_esta_montada_no_compose():
    sql = (DB_DIR / "migrations" / "001_constraints.sql").read_text(encoding="utf-8")
    assert "IF NOT EXISTS" in sql and "SET NOT NULL" in sql
    assert "./backend/database/migrations:/migrations" in COMPOSE


#  PostgreSQL real
PG_URL = os.getenv("TEST_DATABASE_URL", "")


@pytest.mark.skipif(not PG_URL.startswith("postgresql"), reason="requer TEST_DATABASE_URL (PostgreSQL)")
def test_schema_e_seed_aplicam_no_postgres_e_podem_rodar_duas_vezes():
    from sqlalchemy import create_engine, text

    engine = create_engine(PG_URL, isolation_level="AUTOCOMMIT")
    contar = " UNION ALL ".join(f"SELECT '{t}', count(*) FROM {t}" for t in TABELAS)
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
            conn.exec_driver_sql(SCHEMA)
            conn.exec_driver_sql(SEED)
            primeira = dict(conn.execute(text(contar)).all())
            conn.exec_driver_sql(SEED)
            segunda = dict(conn.execute(text(contar)).all())
            assert primeira == segunda
            assert primeira == {"roles": 3, "users": 3, "warehouses": 1, "locations": 5, "products": 3,
                                "stock": 3, "orders": 2, "order_items": 3, "tasks": 1,
                                "optimization_results": 1}
            # sequências ajustadas: o próximo INSERT não pode colidir com o seed
            conn.exec_driver_sql("INSERT INTO products (sku, name) VALUES ('NOVO', 'Novo')")
            conn.exec_driver_sql("INSERT INTO order_items (order_id, product_id, quantity) VALUES (1, 1, 1)")
    finally:
        with engine.begin() as conn:
            conn.exec_driver_sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        engine.dispose()