"""Testes do endpoint POST /optimization/route/batch."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_user
from app.providers.memory import MemoryOrderRouteProvider
from app.routers.optimization_engine import (
    get_order_route_provider,
    get_run_recorder,
    router as optimization_router,
)


class _FakeUser:
    id = 1
    email = "batch@warehouseflow.com"
    is_active = True
    role_name = "ADMIN"


class _NullRecorder:
    def save(self, *args, **kwargs):
        return None


app = FastAPI()
app.include_router(optimization_router)
app.dependency_overrides[get_current_user] = lambda: _FakeUser()
app.dependency_overrides[get_run_recorder] = lambda: _NullRecorder()
app.dependency_overrides[get_order_route_provider] = lambda: MemoryOrderRouteProvider()

client = TestClient(app)


def test_batch_ok_memory_orders():
    response = client.post(
        "/optimization/route/batch",
        json={"order_ids": [1, 2], "workers": 2, "repeats": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["orders_count"] == 2
    assert data["workers"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["order_id"] == 1
    assert data["results"][1]["order_id"] == 2
    assert "two_opt_route" in data["results"][0]["result"]
    assert data["sequential_ms"] > 0
    assert data["parallel_ms"] > 0
    assert data["speedup"] > 0
    assert data["efficiency"] > 0
    assert isinstance(data["native_compiled"], bool)


def test_batch_unknown_order_404():
    response = client.post(
        "/optimization/route/batch",
        json={"order_ids": [1, 999], "workers": 2},
    )
    assert response.status_code == 404


def test_batch_duplicate_ids_400():
    response = client.post(
        "/optimization/route/batch",
        json={"order_ids": [1, 1], "workers": 2},
    )
    assert response.status_code == 400
