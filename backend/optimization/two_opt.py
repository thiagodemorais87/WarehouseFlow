from __future__ import annotations

from optimization.distance import route_distance
from optimization.types import Location


def two_opt_improve(start: Location, route: list[Location]) -> list[Location]:
    """Melhoria local 2-opt: inverte segmentos enquanto a distância diminuir.

    Garante que a distância final seja <= distância da rota de entrada.
    Complexidade: O(N²) por passagem; repete até estabilizar.
    """
    n = len(route)
    if n < 2:
        return list(route)

    best = list(route)
    best_dist = route_distance(start, best)
    improved = True

    while improved:
        improved = False
        for i in range(n - 1):
            for j in range(i + 1, n):
                candidate = best[:i] + best[i : j + 1][::-1] + best[j + 1 :]
                cand_dist = route_distance(start, candidate)
                if cand_dist < best_dist:
                    best = candidate
                    best_dist = cand_dist
                    improved = True
                    break
            if improved:
                break

    return best
