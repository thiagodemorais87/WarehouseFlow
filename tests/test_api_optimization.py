"""Testes do endpoint de otimização — app mínimo com auth mockada."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_user
from app.providers.memory import MemoryOrderRouteProvider
from app.routers.optimization_engine import (
    OptimizationRunRecorder,
    get_order_route_provider,
    get_run_recorder,
    router as optimization_router,
)

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

ACADEMIC_PAYLOAD = {
    "locations": [
        {"id": "FAR1", "x": 10, "y": 0},
        {"id": "NEAR1", "x": 1, "y": 0},
        {"id": "FAR2", "x": 11, "y": 0},
        {"id": "NEAR2", "x": 2, "y": 0},
    ],
    "start": {"id": "START", "x": 0, "y": 0},
}


class _FakeUser:
    id = 1
    email = "test@warehouseflow.com"
    is_active = True
    role_name = "ADMIN"


class _NullRecorder:
    def save(self, *args, **kwargs):
        return None


class _BrokenDbSession:
    """Sessão mínima que falha no commit (histórico best-effort)."""

    def __init__(self) -> None:
        self.rolled_back = False

    def add(self, _obj) -> None:
        return None

    def commit(self) -> None:
        raise RuntimeError("falha simulada ao gravar histórico")

    def rollback(self) -> None:
        self.rolled_back = True


app = FastAPI()
app.include_router(optimization_router)
app.dependency_overrides[get_current_user] = lambda: _FakeUser()
app.dependency_overrides[get_run_recorder] = lambda: _NullRecorder()
# Mantém catálogo acadêmico nos testes de API (provider Postgres coberto em
# test_sqlalchemy_provider.py e testes de integração by-order com DB).
app.dependency_overrides[get_order_route_provider] = lambda: MemoryOrderRouteProvider()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_optimize_route_endpoint_academic_demo():
    response = client.post("/optimization/route", json=ACADEMIC_PAYLOAD)
    assert response.status_code == 200
    data = response.json()

    assert set(data.keys()) == ROUTE_RESPONSE_KEYS
    assert data["original_route"] == ["START", "FAR1", "NEAR1", "FAR2", "NEAR2"]
    assert data["locations_count"] == 4
    assert data["distance_before"] > data["distance_after"]
    assert data["execution_time_ms"] >= 0
    _assert_coherent_metrics(data)


def test_optimize_route_contract_keys_stable_for_frontend():
    response = client.post("/optimization/route", json=ACADEMIC_PAYLOAD)
    assert response.status_code == 200
    assert set(response.json().keys()) == ROUTE_RESPONSE_KEYS


def test_optimize_route_history_write_failure_still_returns_200():
    """Falha ao gravar histórico não interrompe a otimização."""
    broken_db = _BrokenDbSession()
    app.dependency_overrides[get_run_recorder] = (
        lambda: OptimizationRunRecorder(broken_db)
    )
    try:
        response = client.post("/optimization/route", json=ACADEMIC_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == ROUTE_RESPONSE_KEYS
        assert data["locations_count"] == 4
        _assert_coherent_metrics(data)
        assert broken_db.rolled_back is True
    finally:
        app.dependency_overrides[get_run_recorder] = lambda: _NullRecorder()


def test_optimize_route_sample_warehouse_locations():
    payload = {
        "locations": [
            {"id": "A01", "x": 1, "y": 1},
            {"id": "C03", "x": 5, "y": 5},
            {"id": "B02", "x": 2, "y": 2},
            {"id": "D04", "x": 8, "y": 3},
        ],
        "start": {"id": "START", "x": 0, "y": 0},
    }
    response = client.post("/optimization/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["original_route"][0] == "START"
    assert set(data["original_route"][1:]) == {"A01", "C03", "B02", "D04"}
    assert data["distance_after"] == data["two_opt_distance"]


def test_optimize_route_empty_locations():
    payload = {"locations": [], "start": {"id": "START", "x": 0, "y": 0}}
    response = client.post("/optimization/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["locations_count"] == 0
    assert data["distance_before"] == 0
    assert data["reduction_percent"] == 0.0


def test_optimize_route_duplicate_ids_returns_400():
    payload = {
        "locations": [
            {"id": "A01", "x": 1, "y": 1},
            {"id": "A01", "x": 2, "y": 2},
        ],
        "start": {"id": "START", "x": 0, "y": 0},
    }
    response = client.post("/optimization/route", json=payload)
    assert response.status_code == 400
    assert "duplicado" in response.json()["detail"].lower()


def test_optimize_route_by_order_academic_demo():
    payload = {"order_id": 1, "start": {"id": "START", "x": 0, "y": 0}}
    response = client.post("/optimization/route/by-order", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == ROUTE_RESPONSE_KEYS
    assert data["original_route"] == ["START", "FAR1", "NEAR1", "FAR2", "NEAR2"]
    assert data["locations_count"] == 4
    assert data["distance_before"] > data["distance_after"]
    _assert_coherent_metrics(data)


def test_optimize_route_by_order_not_found():
    payload = {"order_id": 999}
    response = client.post("/optimization/route/by-order", json=payload)
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "999" in detail
    assert "não encontrado" in detail.lower()


def test_optimize_route_by_order_without_positions_returns_404():
    app.dependency_overrides[get_order_route_provider] = (
        lambda: MemoryOrderRouteProvider(catalog={50: []})
    )
    try:
        response = client.post(
            "/optimization/route/by-order",
            json={"order_id": 50},
        )
        assert response.status_code == 404
        assert "não possui itens" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides[get_order_route_provider] = (
            lambda: MemoryOrderRouteProvider()
        )


def test_list_pick_locations_for_order():
    response = client.get("/optimization/orders/1/pick-locations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    assert [item["id"] for item in data] == ["FAR1", "NEAR1", "FAR2", "NEAR2"]
    assert data[0]["x"] == 10 and data[0]["y"] == 0


def test_list_pick_locations_not_found():
    response = client.get("/optimization/orders/999/pick-locations")
    assert response.status_code == 404
    assert "999" in response.json()["detail"]