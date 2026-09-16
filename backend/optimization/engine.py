from __future__ import annotations

import time

from optimization.distance import route_distance
from optimization.nearest_neighbor import nearest_neighbor_route
from optimization.two_opt import two_opt_improve
from optimization.types import Location, OptimizationResult

DEFAULT_START = Location(id="START", x=0, y=0)


def _route_ids(start: Location, stops: list[Location]) -> list[str]:
    return [start.id, *[loc.id for loc in stops]]


def optimize_route(
    locations: list[Location],
    start: Location | None = None,
) -> OptimizationResult:
    """Pipeline: rota original → Nearest Neighbor → 2-opt + métricas.

    Reporta distâncias honestamente. O 2-opt nunca piora a rota NN, mas
    `two_opt_distance` pode ser maior que `distance_before` se a ordem
    original já for melhor que a heurística.
    """
    t0 = time.perf_counter()
    start_loc = start if start is not None else DEFAULT_START
    stops = list(locations)

    original_stops = stops
    distance_before = route_distance(start_loc, original_stops)

    nn_stops = nearest_neighbor_route(start_loc, stops)
    nearest_neighbor_distance = route_distance(start_loc, nn_stops)

    two_opt_stops = two_opt_improve(start_loc, nn_stops)
    two_opt_distance = route_distance(start_loc, two_opt_stops)

    distance_after = two_opt_distance
    distance_reduction = distance_before - distance_after
    if distance_before == 0:
        reduction_percent = 0.0
    else:
        reduction_percent = (distance_reduction / distance_before) * 100.0

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    return OptimizationResult(
        original_route=_route_ids(start_loc, original_stops),
        nearest_neighbor_route=_route_ids(start_loc, nn_stops),
        two_opt_route=_route_ids(start_loc, two_opt_stops),
        distance_before=distance_before,
        nearest_neighbor_distance=nearest_neighbor_distance,
        two_opt_distance=two_opt_distance,
        distance_after=distance_after,
        distance_reduction=distance_reduction,
        reduction_percent=reduction_percent,
        execution_time_ms=elapsed_ms,
        locations_count=len(stops),
        start=start_loc,
    )
