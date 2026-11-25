"""Seed final: determinístico, idempotente e coerente com o schema (Sprint 10).

Parte estática: sempre roda. Parte PostgreSQL: requer TEST_DATABASE_URL (banco de
TESTE); usa um schema temporário e não toca no schema público.
"""

import os
import re
from pathlib import Path

import pytest

from app.security import verify_password

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "backend" / "database" / "schema.sql").read_text(encoding="utf-8")
SEED = (ROOT / "backend" / "database" / "seed.sql").read_text(encoding="utf-8")
PG_URL = os.getenv("TEST_DATABASE_URL", "")

TABELAS = ["roles", "users", "warehouses", "locations", "products", "stock", "orders",
           "order_items", "tasks", "optimization_results", "optimization_runs"]

CONTAGENS = {"roles": 3, "users": 3, "warehouses": 1, "locations": 5, "products": 5, "stock": 5,
             "orders": 6, "order_items": 9, "tasks": 4, "optimization_results": 1,
             "optimization_runs": 3}


#  estático
def test_todo_insert_e_idempotente_e_ha_um_por_tabela():
    inserts = re.findall(r"INSERT INTO (\w+)\b.*?;", SEED, re.S)
    assert sorted(inserts) == sorted(TABELAS)
    for bloco in re.findall(r"INSERT INTO \w+.*?;", SEED, re.S):
        assert "ON CONFLICT (id) DO NOTHING" in bloco, bloco[:50]


def test_seed_nao_depende_de_data_ou_valor_aleatorio():
    sem_comentario = re.sub(r"--[^\n]*", "", SEED).lower()
    for proibido in ("now()", "current_timestamp", "random()", "gen_random"):
        assert proibido not in sem_comentario, proibido


@pytest.mark.parametrize("tabela", TABELAS)
def test_sequencia_de_cada_tabela_e_ajustada(tabela):
    assert f"setval('{tabela}_id_seq'" in SEED


def test_senha_de_demo_confere_com_o_hash():
    hashes = set(re.findall(r"'(\$2b\$12\$[^']+)'", SEED))
    assert len(hashes) == 1 and verify_password("admin123", hashes.pop())


def test_seed_so_usa_tabelas_e_colunas_que_o_schema_cria():
    for tabela in TABELAS:
        assert re.search(rf"CREATE TABLE (?:IF NOT EXISTS )?{tabela}\b", SCHEMA), tabela


#  PostgreSQL
@pytest.fixture(scope="module")
def pg():
    """Conexão com schema temporário: schema.sql + seed.sql aplicados DUAS vezes."""
    if not PG_URL.startswith("postgresql"):
        pytest.skip("requer TEST_DATABASE_URL (PostgreSQL)")
    from sqlalchemy import create_engine

    engine = create_engine(PG_URL, isolation_level="AUTOCOMMIT")
    conn = engine.connect()
    conn.exec_driver_sql("DROP SCHEMA IF EXISTS seed_tmp CASCADE")
    conn.exec_driver_sql("CREATE SCHEMA seed_tmp")
    conn.exec_driver_sql("SET search_path TO seed_tmp")
    conn.exec_driver_sql(SCHEMA)
    conn.exec_driver_sql(SEED)
    conn.primeira = _contar(conn)
    conn.exec_driver_sql(SEED)
    conn.segunda = _contar(conn)
    yield conn
    conn.exec_driver_sql("SET search_path TO public")
    conn.exec_driver_sql("DROP SCHEMA IF EXISTS seed_tmp CASCADE")
    conn.close()
    engine.dispose()


def _contar(conn):
    from sqlalchemy import text

    sql = " UNION ALL ".join(f"SELECT '{t}', count(*) FROM {t}" for t in TABELAS)
    return dict(conn.execute(text(sql)).all())


def _q(conn, sql):
    from sqlalchemy import text

    return conn.execute(text(sql)).all()


def test_contagens_do_seed(pg):
    assert pg.primeira == CONTAGENS


def test_rodar_o_seed_de_novo_nao_duplica_nada(pg):
    assert pg.segunda == pg.primeira


def test_demo_cobre_todos_os_status_e_tipos(pg):
    assert dict(_q(pg, "SELECT status, count(*) FROM orders GROUP BY status")) == {
        "PENDING": 2, "PROCESSING": 1, "COMPLETED": 2, "CANCELLED": 1}
    assert dict(_q(pg, "SELECT type, count(*) FROM orders GROUP BY type")) == {"INBOUND": 2, "OUTBOUND": 4}
    assert dict(_q(pg, "SELECT status, count(*) FROM tasks GROUP BY status")) == {
        "PENDING": 2, "IN_PROGRESS": 1, "COMPLETED": 1}
    assert dict(_q(pg, "SELECT type, count(*) FROM tasks GROUP BY type")) == {"PICKING": 3, "PUTAWAY": 1}


def test_demo_tem_estoque_baixo_para_o_dashboard(pg):
    baixos = _q(pg, "SELECT p.sku FROM stock s JOIN products p ON p.id = s.product_id "
                    "WHERE s.quantity <= 10 ORDER BY p.sku")
    assert [r[0] for r in baixos] == ["PROD-004", "PROD-005"]
    assert _q(pg, "SELECT sum(quantity) FROM stock")[0][0] == 164


def test_execucoes_de_otimizacao_sao_coerentes(pg):
    linhas = _q(pg, "SELECT distance_before, distance_after, distance_reduction, reduction_percent, "
                    "locations_count, jsonb_array_length(original_route), jsonb_array_length(two_opt_route), "
                    "user_id, user_email FROM optimization_runs ORDER BY id")
    assert len(linhas) == 3
    for antes, depois, reducao, pct, n, n_orig, n_two, user_id, email in linhas:
        assert reducao == pytest.approx(antes - depois)
        assert pct == pytest.approx(reducao / antes * 100)
        assert n == n_orig == n_two
        assert _q(pg, f"SELECT email FROM users WHERE id = {user_id}")[0][0] == email
    media = _q(pg, "SELECT avg(distance_reduction), avg(reduction_percent) FROM optimization_runs")[0]
    assert float(media[0]) == pytest.approx(44 / 3) and float(media[1]) == pytest.approx(25)


def test_datas_do_seed_sao_fixas_e_ordenadas_para_os_filtros_de_periodo(pg):
    assert _q(pg, "SELECT min(created_at)::date, max(created_at)::date FROM orders")[0] == (
        __import__("datetime").date(2026, 10, 18), __import__("datetime").date(2026, 10, 28))
    assert _q(pg, "SELECT count(*) FROM orders WHERE created_at >= '2026-10-26' AND created_at < '2026-10-29'")[0][0] == 3


def test_proximo_id_gerado_apos_o_seed_nao_colide(pg):
    pg.exec_driver_sql("INSERT INTO products (sku, name) VALUES ('NOVO-1', 'Novo')")
    pg.exec_driver_sql("INSERT INTO orders (type, status) VALUES ('INBOUND', 'PENDING')")
    pg.exec_driver_sql("INSERT INTO order_items (order_id, product_id, quantity) VALUES (1, 1, 1)")
    pg.exec_driver_sql("INSERT INTO optimization_runs (user_id, user_email, source, original_route, "
                       "nearest_neighbor_route, two_opt_route, distance_before, nearest_neighbor_distance, "
                       "two_opt_distance, distance_after, distance_reduction, reduction_percent, "
                       "execution_time_ms, locations_count) VALUES (1,'a@b.com','route','[]','[]','[]',1,1,1,1,0,0,0,0)")
    assert _q(pg, "SELECT max(id) FROM optimization_runs")[0][0] == 4