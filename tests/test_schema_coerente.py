"""Schema final coerente com o código (checklist da Sprint 10).

Aplica o DDL oficial (backend/database/schema.sql, o mesmo usado pelo Compose)
num PostgreSQL real e compara com os modelos SQLAlchemy: tabelas, colunas,
tipos, NOT NULL, PK, FK (com ON DELETE), UNIQUE e CHECK.

Requer TEST_DATABASE_URL apontando para um PostgreSQL de TESTE. O teste usa um
schema temporário (`drift_check`) e não toca nas tabelas do schema público.
"""

import os
import re
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, types as sqltypes

import app.models  # noqa: F401  (registra as tabelas)
import app.models.optimization_run  # noqa: F401
from app.database import Base

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = (ROOT / "backend" / "database" / "schema.sql").read_text(encoding="utf-8")
PG_URL = os.getenv("TEST_DATABASE_URL", "")

TMP_SCHEMA = "drift_check"


def _familia(tipo) -> str:
    """Agrupa tipos equivalentes (VARCHAR/TEXT/Enum, JSON/JSONB, FLOAT/DOUBLE...)."""
    if isinstance(tipo, sqltypes.Boolean):
        return "bool"
    if isinstance(tipo, sqltypes.Integer):
        return "int"
    if isinstance(tipo, sqltypes.Numeric) and not isinstance(tipo, sqltypes.Float):
        return "numeric"
    if isinstance(tipo, sqltypes.Float):
        return "float"
    if isinstance(tipo, sqltypes.DateTime):
        return "datetime"
    if isinstance(tipo, sqltypes.JSON):
        return "json"
    if isinstance(tipo, sqltypes.String):  # inclui Text e Enum (native_enum=False)
        return "text"
    return type(tipo).__name__.lower()


@pytest.fixture(scope="module")
def db():
    """Conexão sobre um schema temporário com o schema.sql aplicado."""
    if not PG_URL.startswith("postgresql"):
        pytest.skip("requer TEST_DATABASE_URL (PostgreSQL)")
    engine = create_engine(PG_URL, isolation_level="AUTOCOMMIT")
    conn = engine.connect()
    conn.exec_driver_sql(f"DROP SCHEMA IF EXISTS {TMP_SCHEMA} CASCADE")
    conn.exec_driver_sql(f"CREATE SCHEMA {TMP_SCHEMA}")
    conn.exec_driver_sql(f"SET search_path TO {TMP_SCHEMA}")
    conn.exec_driver_sql(SCHEMA_SQL)
    yield conn
    conn.exec_driver_sql("SET search_path TO public")
    conn.exec_driver_sql(f"DROP SCHEMA IF EXISTS {TMP_SCHEMA} CASCADE")
    conn.close()
    engine.dispose()


def test_mesmas_tabelas(db):
    db = inspect(db)
    assert set(db.get_table_names(TMP_SCHEMA)) == set(Base.metadata.tables)


@pytest.mark.parametrize("tabela", sorted(Base.metadata.tables))
def test_colunas_tipos_e_nulidade(db, tabela):
    db = inspect(db)
    modelo = Base.metadata.tables[tabela]
    banco = {c["name"]: c for c in db.get_columns(tabela, TMP_SCHEMA)}
    assert set(banco) == {c.name for c in modelo.columns}, "colunas diferentes"
    for col in modelo.columns:
        real = banco[col.name]
        assert _familia(real["type"]) == _familia(col.type), (
            f"{tabela}.{col.name}: banco={real['type']} modelo={col.type}"
        )
        assert real["nullable"] == col.nullable or col.primary_key, (
            f"{tabela}.{col.name}: nullable banco={real['nullable']} modelo={col.nullable}"
        )
        # Enum não nativo: o SQLAlchemy usa o maior valor como tamanho; o banco é mais largo de propósito
        comp_banco = getattr(real["type"], "length", None)
        comp_modelo = None if isinstance(col.type, sqltypes.Enum) else getattr(col.type, "length", None)
        if comp_banco and comp_modelo:
            assert comp_banco == comp_modelo, f"{tabela}.{col.name}: VARCHAR({comp_banco}) x ({comp_modelo})"


@pytest.mark.parametrize("tabela", sorted(Base.metadata.tables))
def test_chave_primaria(db, tabela):
    db = inspect(db)
    modelo = [c.name for c in Base.metadata.tables[tabela].primary_key.columns]
    assert db.get_pk_constraint(tabela, TMP_SCHEMA)["constrained_columns"] == modelo


@pytest.mark.parametrize("tabela", sorted(Base.metadata.tables))
def test_chaves_estrangeiras_e_on_delete(db, tabela):
    db = inspect(db)
    def regra(valor):
        return (valor or "NO ACTION").upper()

    esperado = {
        (fk.parent.name, fk.column.table.name, fk.column.name, regra(fk.ondelete))
        for fk in Base.metadata.tables[tabela].foreign_keys
    }
    real = {
        (fk["constrained_columns"][0], fk["referred_table"], fk["referred_columns"][0],
         regra(fk["options"].get("ondelete")))
        for fk in db.get_foreign_keys(tabela, TMP_SCHEMA)
    }
    assert real == esperado


@pytest.mark.parametrize("tabela", sorted(Base.metadata.tables))
def test_unicidade(db, tabela):
    db = inspect(db)
    modelo = Base.metadata.tables[tabela]
    esperado = {tuple(sorted(c.name for c in u.columns))
                for u in modelo.constraints if u.__class__.__name__ == "UniqueConstraint"}
    esperado |= {(c.name,) for c in modelo.columns if c.unique}
    real = {tuple(sorted(u["column_names"])) for u in db.get_unique_constraints(tabela, TMP_SCHEMA)}
    assert real == esperado


@pytest.mark.parametrize("tabela", sorted(Base.metadata.tables))
def test_checks_com_o_mesmo_nome(db, tabela):
    db = inspect(db)
    modelo = Base.metadata.tables[tabela]
    esperado = {c.name for c in modelo.constraints if c.__class__.__name__ == "CheckConstraint"}
    real = {c["name"] for c in db.get_check_constraints(tabela, TMP_SCHEMA)}
    assert real == esperado


def test_ddl_do_optimization_runs_existe_uma_unica_vez():
    """Duas cópias do mesmo CREATE TABLE são uma fonte de divergência."""
    assert len(re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?optimization_runs\b", SCHEMA_SQL)) == 1


def _normaliza(sql: str) -> list[str]:
    """Remove comentários e espaços para comparar só os comandos."""
    sem_comentario = re.sub(r"--[^\n]*", "", sql)
    return [" ".join(cmd.split()) for cmd in sem_comentario.split(";") if cmd.strip()]


def test_optimization_runs_sql_e_identico_ao_trecho_do_schema():
    """O arquivo dedicado (para bancos antigos) não pode divergir do DDL oficial."""
    avulso = _normaliza((ROOT / "backend" / "database" / "optimization_runs.sql").read_text(encoding="utf-8"))
    oficial = [c for c in _normaliza(SCHEMA_SQL) if "optimization_runs" in c]
    assert avulso == oficial


def test_compose_monta_so_o_schema_como_ddl_oficial():
    """schema.sql é o DDL oficial; seed e optimization_runs (legado/idempotente) no initdb.d."""
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "01-schema.sql" in compose and "02-seed.sql" in compose
    assert "03-optimization_runs.sql" in compose
    assert "./backend/database/migrations:/migrations" in compose


def test_orm_grava_e_le_optimization_runs_no_ddl_oficial(db):
    """O modelo (ORM) precisa conseguir gravar nas colunas JSONB criadas pelo schema.sql."""
    from datetime import datetime

    from sqlalchemy.orm import Session

    from app.models.optimization_run import OptimizationRun

    with Session(bind=db) as sessao:
        sessao.add(OptimizationRun(
            user_id=1, user_email="a@b.com", executed_at=datetime(2026, 10, 5, 9, 0), source="route",
            original_route=["A", "B", "C"], nearest_neighbor_route=["A", "C", "B"], two_opt_route=["A", "B", "C"],
            distance_before=10.0, nearest_neighbor_distance=8.0, two_opt_distance=6.0, distance_after=6.0,
            distance_reduction=4.0, reduction_percent=40.0, execution_time_ms=1.5, locations_count=3,
        ))
        sessao.commit()
        run = sessao.query(OptimizationRun).one()
        assert run.original_route == ["A", "B", "C"] and run.order_id is None
        sessao.delete(run)
        sessao.commit()


def test_ddl_lido_pelo_gerador_do_pdf_tem_as_mesmas_colunas_dos_modelos():
    """O PDF/Mermaid é gerado a partir do schema.sql: ele não pode divergir dos modelos."""
    pytest.importorskip("reportlab")
    import importlib.util

    spec = importlib.util.spec_from_file_location("gerador_pdf", ROOT / "scripts" / "gerar_pdf_relacionamentos.py")
    gerador = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gerador)
    ddl = gerador.ler_ddl()
    assert set(ddl) == set(Base.metadata.tables)
    for tabela, colunas in ddl.items():
        assert list(colunas) == [c.name for c in Base.metadata.tables[tabela].columns], tabela