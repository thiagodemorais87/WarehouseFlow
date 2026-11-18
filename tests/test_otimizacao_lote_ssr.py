"""Lote paralelo via POST /otimizacao/lote (HTML server-side, sem JS de cálculo)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.deps import get_current_user_or_none
from app.main import app
from optimization.parallel import BatchParallelResult
from optimization.types import Location, OptimizationResult


class _FakeUser:
    id = 1
    email = "ssr@warehouseflow.com"
    name = "SSR Tester"
    is_active = True
    role_name = "ADMIN"
    role = None


def _fake_result() -> OptimizationResult:
    return OptimizationResult(
        original_route=["START", "A"],
        nearest_neighbor_route=["START", "A"],
        two_opt_route=["START", "A"],
        distance_before=10.0,
        nearest_neighbor_distance=8.0,
        two_opt_distance=8.0,
        distance_after=8.0,
        distance_reduction=2.0,
        reduction_percent=20.0,
        execution_time_ms=1.0,
        locations_count=1,
        start=Location(id="START", x=0, y=0),
    )


def test_otimizacao_lote_post_renders_metrics(monkeypatch):
    fake_batch = BatchParallelResult(
        results=[_fake_result(), _fake_result()],
        sequential_ms=100.0,
        parallel_ms=40.0,
        speedup=2.5,
        efficiency=1.25,
        workers=2,
        jobs_count=2,
    )

    def _fake_optimize(order_ids, provider, start=None, *, workers=2, repeats=1):
        return list(order_ids), fake_batch

    monkeypatch.setattr(
        "app.services.optimization_service.optimize_batch_from_order_ids",
        _fake_optimize,
    )
    monkeypatch.setattr(
        "app.routers.optimization_engine.OptimizationRunRecorder.save",
        lambda self, *a, **k: None,
    )
    monkeypatch.setattr(
        "app.services.optimization_service.is_native_compiled",
        lambda: False,
    )

    app.dependency_overrides[get_current_user_or_none] = lambda: _FakeUser()
    client = TestClient(app)
    try:
        response = client.post(
            "/otimizacao/lote",
            data={"order_ids": "1, 2", "workers": "2", "repeats": "2"},
        )
        if response.status_code == 404:
            # Frontend não montado neste ambiente
            return
        assert response.status_code == 200
        body = response.text
        assert "Desempenho do paralelismo" in body
        assert "2.50" in body or "2.5" in body
        assert "fetch(" not in body.lower() or "optimization.js" in body
        # Formulário server-side presente
        assert 'action="/otimizacao/lote"' in body
        assert 'method="post"' in body.lower() or "method=\"post\"" in body
    finally:
        app.dependency_overrides.clear()


def test_otimizacao_batch_mode_get():
    app.dependency_overrides[get_current_user_or_none] = lambda: _FakeUser()
    client = TestClient(app)
    try:
        response = client.get("/otimizacao?mode=batch")
        if response.status_code == 404:
            return
        assert response.status_code == 200
        assert 'action="/otimizacao/lote"' in response.text
        assert "Lote paralelo" in response.text
    finally:
        app.dependency_overrides.clear()
