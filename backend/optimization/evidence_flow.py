"""Evidência reproduzível do fluxo do motor (sem UI / sem Postgres compartilhado).

Fluxo: POST /optimization/route → summary → picking → CSV.
Imprime redução média e encerra com exit 0 se tudo ok.

Uso (raiz do repositório):

    python -m optimization.evidence_flow

    # ou (Windows PowerShell):
    $env:PYTHONPATH = "backend"; python backend/optimization/evidence_flow.py
"""

from __future__ import annotations

import os
import sys

# Ao executar como arquivo sob backend/optimization/, o cwd do script entra em
# sys.path[0] e sombreia o módulo stdlib `types` com optimization/types.py.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if sys.path and os.path.abspath(sys.path[0]) == os.path.abspath(_THIS_DIR):
    sys.path.pop(0)
_BACKEND = os.path.dirname(_THIS_DIR)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "evidence-secret")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.deps import get_current_user
from app.models.optimization_run import OptimizationRun  # noqa: F401
from app.routers.optimization_engine import router as optimization_router

PAYLOAD = {
    "locations": [
        {"id": "FAR1", "x": 10, "y": 0},
        {"id": "NEAR1", "x": 1, "y": 0},
        {"id": "FAR2", "x": 11, "y": 0},
        {"id": "NEAR2", "x": 2, "y": 0},
    ],
    "start": {"id": "START", "x": 0, "y": 0},
}


class _FakeUser:
    id = 7
    email = "evidencia@warehouseflow.com"
    is_active = True
    role_name = "OPERADOR"


def _build_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(optimization_router)
    app.dependency_overrides[get_current_user] = lambda: _FakeUser()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def main() -> int:
    client = _build_client()

    print("=== 1) Otimização POST /optimization/route ===")
    optimized = client.post("/optimization/route", json=PAYLOAD)
    if optimized.status_code != 200:
        print("FALHA otimização:", optimized.status_code, optimized.text)
        return 1
    metrics = optimized.json()
    print(f"  distance_before={metrics['distance_before']}")
    print(f"  distance_after={metrics['distance_after']}")
    print(f"  distance_reduction={metrics['distance_reduction']}")
    print(f"  reduction_percent={metrics['reduction_percent']}")
    print(f"  two_opt_route={' > '.join(metrics['two_opt_route'])}")

    print("=== 2) Summary GET /optimization/reports/summary ===")
    summary = client.get("/optimization/reports/summary")
    if summary.status_code != 200:
        print("FALHA summary:", summary.status_code, summary.text)
        return 1
    summary_body = summary.json()
    runs_count = summary_body["runs_count"]
    avg_pct = summary_body["average_reduction_percent"]
    avg_dist = summary_body["average_distance_reduction"]
    print(f"  runs_count={runs_count}")
    print(f"  average_distance_reduction={avg_dist}")
    print(f"  average_reduction_percent={avg_pct}")
    if runs_count < 1:
        print("FALHA: histórico vazio após otimização")
        return 1

    print("=== 3) Picking GET /optimization/reports/picking ===")
    picking = client.get("/optimization/reports/picking")
    if picking.status_code != 200:
        print("FALHA picking:", picking.status_code, picking.text)
        return 1
    rows = picking.json()
    if len(rows) < 1:
        print("FALHA: nenhum run no picking")
        return 1
    print(f"  runs={len(rows)} source={rows[0]['source']} user={rows[0]['user_email']}")

    print("=== 4) CSV GET /optimization/reports/picking.csv ===")
    csv_response = client.get("/optimization/reports/picking.csv")
    if csv_response.status_code != 200:
        print("FALHA csv:", csv_response.status_code, csv_response.text)
        return 1
    text = csv_response.text
    header = text.splitlines()[0] if text else ""
    if "two_opt_route" not in header:
        print("FALHA: header CSV sem two_opt_route")
        return 1
    route_cell = " > ".join(metrics["two_opt_route"])
    if route_cell not in text:
        print("FALHA: rota otimizada ausente no CSV")
        return 1
    print(f"  content-type={csv_response.headers.get('content-type')}")
    print(f"  linhas={len(text.splitlines())}")

    print()
    print("EVIDÊNCIA OK")
    print(f"  otimização: reduction_percent={metrics['reduction_percent']}")
    print(f"  redução média (summary): {avg_pct}% em {runs_count} run(s)")
    print("  picking + CSV: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
