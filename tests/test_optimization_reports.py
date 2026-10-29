"""Histórico, média de redução e CSV do motor de otimização."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.deps import get_current_user
from app.models.optimization_run import OptimizationRun  # noqa: F401
from app.routers.optimization_engine import router as optimization_router


class _FakeUser:
    id = 7
    email = "operador@warehouseflow.com"
    is_active = True
    role_name = "OPERADOR"


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
client = TestClient(app)

PAYLOAD = {
    "locations": [
        {"id": "FAR1", "x": 10, "y": 0},
        {"id": "NEAR1", "x": 1, "y": 0},
        {"id": "FAR2", "x": 11, "y": 0},
        {"id": "NEAR2", "x": 2, "y": 0},
    ],
    "start": {"id": "START", "x": 0, "y": 0},
}

SUMMARY_KEYS = {
    "runs_count",
    "average_distance_reduction",
    "average_reduction_percent",
}

PICKING_RUN_KEYS = {
    "id",
    "user_id",
    "user_email",
    "executed_at",
    "source",
    "order_id",
    "original_route",
    "nearest_neighbor_route",
    "two_opt_route",
    "distance_before",
    "nearest_neighbor_distance",
    "two_opt_distance",
    "distance_after",
    "distance_reduction",
    "reduction_percent",
    "execution_time_ms",
    "locations_count",
}

# Campos que picking-report.js / dashboard.js leem (contrato FE estável).
FE_SUMMARY_KEYS = SUMMARY_KEYS
FE_PICKING_TABLE_KEYS = {
    "executed_at",
    "user_id",
    "order_id",
    "source",
    "locations_count",
    "distance_before",
    "distance_after",
    "reduction_percent",
    "execution_time_ms",
    "two_opt_route",
}


def test_route_is_recorded_and_reported():
    empty = client.get("/optimization/reports/summary")
    assert empty.status_code == 200
    empty_body = empty.json()
    assert set(empty_body.keys()) == SUMMARY_KEYS
    assert empty_body["runs_count"] == 0
    assert empty_body["average_distance_reduction"] == 0
    assert empty_body["average_reduction_percent"] == 0

    optimized = client.post("/optimization/route", json=PAYLOAD)
    assert optimized.status_code == 200
    metrics = optimized.json()

    summary = client.get("/optimization/reports/summary")
    assert summary.status_code == 200
    summary_body = summary.json()
    assert set(summary_body.keys()) == SUMMARY_KEYS
    assert FE_SUMMARY_KEYS <= set(summary_body.keys())
    assert summary_body["runs_count"] == 1
    assert summary_body["average_distance_reduction"] == metrics["distance_reduction"]
    assert summary_body["average_reduction_percent"] == metrics["reduction_percent"]

    report = client.get("/optimization/reports/picking")
    assert report.status_code == 200
    rows = report.json()
    assert len(rows) == 1
    row = rows[0]
    assert set(row.keys()) == PICKING_RUN_KEYS
    assert FE_PICKING_TABLE_KEYS <= set(row.keys())
    assert row["user_id"] == 7
    assert row["user_email"] == "operador@warehouseflow.com"
    assert row["source"] == "route"
    assert row["original_route"] == metrics["original_route"]
    assert row["nearest_neighbor_route"] == metrics["nearest_neighbor_route"]
    assert row["two_opt_route"] == metrics["two_opt_route"]
    assert row["execution_time_ms"] == metrics["execution_time_ms"]
    assert row["executed_at"]

    csv_response = client.get("/optimization/reports/picking.csv")
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    text = csv_response.text
    assert "two_opt_route" in text.splitlines()[0]
    assert " > ".join(metrics["two_opt_route"]) in text
    assert "operador@warehouseflow.com" in text


def test_reports_contract_keys_stable_for_frontend():
    """Garante shape JSON consumido por picking-report.js / dashboard."""
    client.post("/optimization/route", json=PAYLOAD)

    summary = client.get("/optimization/reports/summary").json()
    assert FE_SUMMARY_KEYS <= set(summary.keys())

    rows = client.get("/optimization/reports/picking").json()
    assert rows
    assert FE_PICKING_TABLE_KEYS <= set(rows[0].keys())
