"""Testes do lote paralelo (ProcessPool) + métricas S(p)/E(p)."""

from __future__ import annotations

from optimization.engine import optimize_route
from optimization.native_status import native_compiled
from optimization.parallel import optimize_routes_batch, optimize_routes_sequential
from optimization.types import Location


def _grid_job(seed: int, n: int = 24) -> tuple[list[Location], Location]:
    start = Location(id="START", x=0.0, y=0.0)
    # Ordem “ruim” para forçar trabalho NN+2-opt
    locations = [
        Location(id=f"P{seed}-{i}", x=float((i * 7 + seed) % 17), y=float((i * 3 + seed) % 13))
        for i in range(n)
    ]
    return locations, start


def test_native_status_is_bool():
    assert isinstance(native_compiled(), bool)


def test_batch_empty():
    result = optimize_routes_batch([])
    assert result.jobs_count == 0
    assert result.results == []
    assert result.speedup == 1.0


def test_batch_matches_single_optimize_route():
    locations, start = _grid_job(1, n=12)
    expected = optimize_route(locations, start=start)
    batch = optimize_routes_batch([(locations, start)], workers=1)
    assert len(batch.results) == 1
    got = batch.results[0]
    assert got.two_opt_route == expected.two_opt_route
    assert got.distance_after == expected.distance_after
    assert got.distance_before == expected.distance_before


def test_batch_parallel_metrics_and_equivalence():
    jobs = [_grid_job(i, n=20) for i in range(4)]
    sequential = optimize_routes_sequential(jobs, repeats=3)
    batch = optimize_routes_batch(jobs, workers=2, repeats=3)

    assert batch.jobs_count == 4
    assert batch.workers == 2
    assert len(batch.results) == 4
    assert batch.sequential_ms > 0
    assert batch.parallel_ms > 0
    assert batch.speedup > 0
    assert batch.efficiency > 0

    for seq, par in zip(sequential, batch.results):
        assert seq.two_opt_route == par.two_opt_route
        assert seq.distance_after == par.distance_after
        assert seq.distance_before == par.distance_before


def test_batch_reports_positive_timing_with_workers():
    """Garante medição T(1)/T(p) com pool; S(p) depende da máquina (demo na UI)."""
    jobs = [_grid_job(i, n=20) for i in range(4)]
    batch = optimize_routes_batch(jobs, workers=2, repeats=4)
    assert batch.workers == 2
    assert batch.sequential_ms > 0
    assert batch.parallel_ms > 0
    assert batch.speedup > 0
    assert batch.efficiency > 0
