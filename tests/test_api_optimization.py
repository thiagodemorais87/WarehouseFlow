from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_optimize_route_endpoint_academic_demo():
    payload = {
        "locations": [
            {"id": "FAR1", "x": 10, "y": 0},
            {"id": "NEAR1", "x": 1, "y": 0},
            {"id": "FAR2", "x": 11, "y": 0},
            {"id": "NEAR2", "x": 2, "y": 0},
        ],
        "start": {"id": "START", "x": 0, "y": 0},
    }
    response = client.post("/optimization/route", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["original_route"] == ["START", "FAR1", "NEAR1", "FAR2", "NEAR2"]
    assert data["locations_count"] == 4
    assert data["distance_before"] > data["distance_after"]
    assert data["two_opt_distance"] <= data["nearest_neighbor_distance"]
    assert data["distance_reduction"] == data["distance_before"] - data["distance_after"]
    assert data["execution_time_ms"] >= 0


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
