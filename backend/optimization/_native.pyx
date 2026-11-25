# cython: language_level=3
"""Hot path compilado do motor (Manhattan + distância de rota)."""


def manhattan(a, b):
    """Distância Manhattan entre duas posições com atributos x/y."""
    return abs(a.x - b.x) + abs(a.y - b.y)


def route_distance(start, stops):
    """Distância total START → stop1 → … → stopN."""
    n = len(stops)
    if n == 0:
        return 0.0
    total = abs(start.x - stops[0].x) + abs(start.y - stops[0].y)
    i = 0
    while i < n - 1:
        total += abs(stops[i].x - stops[i + 1].x) + abs(stops[i].y - stops[i + 1].y)
        i += 1
    return total


def is_compiled():
    return True
