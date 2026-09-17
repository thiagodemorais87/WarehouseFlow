from __future__ import annotations

from optimization.distance import manhattan
from optimization.types import Location


def nearest_neighbor_route(start: Location, locations: list[Location]) -> list[Location]:
    """Constrói rota gulosa: sempre visita o não-visitado mais próximo.

    Empates de distância são resolvidos pelo menor `id` (determinismo).
    Complexidade: O(N²).
    """
    if not locations:
        return []

    remaining = list(locations)
    route: list[Location] = []
    current = start

    while remaining:
        best_idx = 0
        best_dist = manhattan(current, remaining[0])
        best_id = remaining[0].id
        for i in range(1, len(remaining)):
            cand = remaining[i]
            d = manhattan(current, cand)
            if d < best_dist or (d == best_dist and cand.id < best_id):
                best_idx = i
                best_dist = d
                best_id = cand.id
        next_loc = remaining.pop(best_idx)
        route.append(next_loc)
        current = next_loc

    return route
