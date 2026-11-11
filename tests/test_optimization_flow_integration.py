"""Fluxo integrado do motor: posições → by-order → summary/picking/CSV.

Cobre a navegação Sprint 09 só via API (sem FE):
pedido → pick-locations → otimizar → histórico/relatório.
"""

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
from app.providers.memory import MemoryOrderRouteProvider
from app.routers.optimization_engine import (
    get_order_route_provider,
    router as optimization_router,
)

ORDER_ID = 1
EXPECTED_LOCATION_IDS = ["FAR1", "NEAR1", "FAR2", "NEAR2"]

ROUTE_RESPONSE_KEYS = {
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
app.dependency_overrides[get_order_route_provider] = lambda: MemoryOrderRouteProvider()
client = TestClient(app)


def _assert_coherent_metrics(data: dict) -> None:
    assert data["distance_after"] == data["two_opt_distance"]
    assert data["distance_reduction"] == data["distance_before"] - data["distance_after"]
    assert data["two_opt_distance"] <= data["nearest_neighbor_distance"]
    if data["distance_before"] == 0:
        assert data["reduction_percent"] == 0.0
    else:
        expected = (data["distance_reduction"] / data["distance_before"]) * 100.0
        assert abs(data["reduction_percent"] - expected) < 1e-9


def test_order_positions_optimize_history_csv_flow():
    """pedido → posições → otimizar → summary/picking/CSV."""
    positions = client.get(f"/optimization/orders/{ORDER_ID}/pick-locations")
    assert positions.status_code == 200
    locations = positions.json()
    assert [item["id"] for item in locations] == EXPECTED_LOCATION_IDS
    assert all("x" in item and "y" in item for item in locations)

    optimized = client.post(
        "/optimization/route/by-order",
        json={"order_id": ORDER_ID, "start": {"id": "START", "x": 0, "y": 0}},
    )
    assert optimized.status_code == 200
    metrics = optimized.json()
    assert set(metrics.keys()) == ROUTE_RESPONSE_KEYS
    assert metrics["original_route"] == ["START", *EXPECTED_LOCATION_IDS]
    assert metrics["locations_count"] == len(EXPECTED_LOCATION_IDS)
    assert metrics["distance_before"] > metrics["distance_after"]
    _assert_coherent_metrics(metrics)

    summary = client.get("/optimization/reports/summary")
    assert summary.status_code == 200
    summary_body = summary.json()
    assert set(summary_body.keys()) == SUMMARY_KEYS
    assert summary_body["runs_count"] >= 1
    assert summary_body["average_distance_reduction"] == metrics["distance_reduction"]
    assert summary_body["average_reduction_percent"] == metrics["reduction_percent"]

    report = client.get("/optimization/reports/picking")
    assert report.status_code == 200
    rows = report.json()
    assert rows
    row = rows[0]
    assert set(row.keys()) == PICKING_RUN_KEYS
    assert row["source"] == "by-order"
    assert row["order_id"] == ORDER_ID
    assert row["user_id"] == 7
    assert row["user_email"] == "operador@warehouseflow.com"
    assert row["original_route"] == metrics["original_route"]
    assert row["nearest_neighbor_route"] == metrics["nearest_neighbor_route"]
    assert row["two_opt_route"] == metrics["two_opt_route"]
    assert row["distance_before"] == metrics["distance_before"]
    assert row["distance_after"] == metrics["distance_after"]
    assert row["reduction_percent"] == metrics["reduction_percent"]
    assert row["execution_time_ms"] == metrics["execution_time_ms"]
    assert row["executed_at"]

    csv_response = client.get("/optimization/reports/picking.csv")
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    text = csv_response.text
    header = text.splitlines()[0]
    assert "order_id" in header
    assert "two_opt_route" in header
    assert "source" in header
    assert str(ORDER_ID) in text
    assert "by-order" in text
    assert " > ".join(metrics["two_opt_route"]) in text
    assert "operador@warehouseflow.com" in text
