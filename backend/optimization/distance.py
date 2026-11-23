from __future__ import annotations

from optimization.types import Location

try:
    from optimization._native import manhattan as _manhattan_impl
    from optimization._native import route_distance as _route_distance_impl
except ImportError:
    try:
        from _native import manhattan as _manhattan_impl
        from _native import route_distance as _route_distance_impl
    except ImportError:
        _manhattan_impl = None
        _route_distance_impl = None


def manhattan(a: Location, b: Location) -> float:
    """Distância Manhattan entre duas posições (corredores do armazém)."""
    if _manhattan_impl is not None:
        return float(_manhattan_impl(a, b))
    return abs(a.x - b.x) + abs(a.y - b.y)


def route_distance(start: Location, stops: list[Location]) -> float:
    """Distância total START → stop1 → stop2 → ... → stopN."""
    if _route_distance_impl is not None:
        return float(_route_distance_impl(start, stops))
    if not stops:
        return 0.0
    total = manhattan(start, stops[0])
    for i in range(len(stops) - 1):
        total += manhattan(stops[i], stops[i + 1])
    return total
