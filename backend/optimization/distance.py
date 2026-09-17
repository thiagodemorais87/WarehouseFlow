from __future__ import annotations

from optimization.types import Location


def manhattan(a: Location, b: Location) -> float:
    """Distância Manhattan entre duas posições (corredores do armazém)."""
    return abs(a.x - b.x) + abs(a.y - b.y)


def route_distance(start: Location, stops: list[Location]) -> float:
    """Distância total START → stop1 → stop2 → ... → stopN."""
    if not stops:
        return 0.0
    total = manhattan(start, stops[0])
    for i in range(len(stops) - 1):
        total += manhattan(stops[i], stops[i + 1])
    return total
