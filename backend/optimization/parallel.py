"""Lote de otimizações com medição sequencial vs ProcessPool."""

from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from optimization.engine import optimize_route
from optimization.types import Location, OptimizationResult


@dataclass(slots=True)
class BatchParallelResult:
    results: list[OptimizationResult]
    sequential_ms: float
    parallel_ms: float
    speedup: float
    efficiency: float
    workers: int
    jobs_count: int


def _location_to_payload(loc: Location) -> dict:
    return {"id": loc.id, "x": loc.x, "y": loc.y}


def _payload_to_location(data: dict) -> Location:
    return Location(id=data["id"], x=float(data["x"]), y=float(data["y"]))


def _job_to_payload(
    locations: list[Location],
    start: Location | None,
    repeats: int,
) -> dict:
    return {
        "locations": [_location_to_payload(loc) for loc in locations],
        "start": _location_to_payload(start) if start is not None else None,
        "repeats": max(1, int(repeats)),
    }


def _optimize_job(payload: dict) -> OptimizationResult:
    """Worker top-level (picklável no Windows)."""
    locations = [_payload_to_location(item) for item in payload["locations"]]
    start = (
        _payload_to_location(payload["start"])
        if payload.get("start") is not None
        else None
    )
    repeats = max(1, int(payload.get("repeats", 1)))
    result: OptimizationResult | None = None
    for _ in range(repeats):
        result = optimize_route(locations, start=start)
    assert result is not None
    return result


def optimize_routes_batch(
    jobs: list[tuple[list[Location], Location | None]],
    *,
    workers: int | None = None,
    repeats: int = 1,
) -> BatchParallelResult:
    """Otimiza N rotas: baseline sequencial + paralelo; devolve S(p) e E(p)."""
    if not jobs:
        return BatchParallelResult(
            results=[],
            sequential_ms=0.0,
            parallel_ms=0.0,
            speedup=1.0,
            efficiency=1.0,
            workers=1,
            jobs_count=0,
        )

    payloads = [
        _job_to_payload(locations, start, repeats) for locations, start in jobs
    ]
    worker_count = workers if workers is not None else (os.cpu_count() or 2)
    worker_count = max(1, min(int(worker_count), len(payloads)))

    t0 = time.perf_counter()
    sequential_results = [_optimize_job(payload) for payload in payloads]
    sequential_ms = (time.perf_counter() - t0) * 1000.0

    if worker_count == 1 or len(payloads) == 1:
        t1 = time.perf_counter()
        parallel_results = [_optimize_job(payload) for payload in payloads]
        parallel_ms = (time.perf_counter() - t1) * 1000.0
    else:
        # Warm-up dos workers (spawn no Windows é caro; não entra em T(p))
        with ProcessPoolExecutor(max_workers=worker_count) as pool:
            list(pool.map(_optimize_job, [payloads[0]]))
            t1 = time.perf_counter()
            parallel_results = list(pool.map(_optimize_job, payloads))
            parallel_ms = (time.perf_counter() - t1) * 1000.0


    if parallel_ms > 0:
        speedup = sequential_ms / parallel_ms
    else:
        speedup = 1.0
    efficiency = speedup / worker_count if worker_count else 0.0

    # Correção: resultados do paralelo (mesma lógica; métricas de rota iguais)
    return BatchParallelResult(
        results=parallel_results,
        sequential_ms=sequential_ms,
        parallel_ms=parallel_ms,
        speedup=speedup,
        efficiency=efficiency,
        workers=worker_count,
        jobs_count=len(jobs),
    )


# Mantém referência usada nos testes de equivalência sequencial
def optimize_routes_sequential(
    jobs: list[tuple[list[Location], Location | None]],
    *,
    repeats: int = 1,
) -> list[OptimizationResult]:
    payloads = [
        _job_to_payload(locations, start, repeats) for locations, start in jobs
    ]
    return [_optimize_job(payload) for payload in payloads]
