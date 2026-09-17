from optimization.distance import manhattan, route_distance
from optimization.types import Location


def test_manhattan_basic():
    a = Location(id="A", x=1, y=2)
    b = Location(id="B", x=5, y=4)
    assert manhattan(a, b) == 6


def test_manhattan_symmetric():
    a = Location(id="A", x=0, y=0)
    b = Location(id="B", x=3, y=4)
    assert manhattan(a, b) == manhattan(b, a) == 7


def test_manhattan_same_point():
    a = Location(id="A", x=2, y=2)
    assert manhattan(a, a) == 0


def test_route_distance_empty_after_start():
    start = Location(id="START", x=0, y=0)
    assert route_distance(start, []) == 0


def test_route_distance_single_stop():
    start = Location(id="START", x=0, y=0)
    a = Location(id="A01", x=3, y=4)
    assert route_distance(start, [a]) == 7


def test_route_distance_multiple_stops():
    start = Location(id="START", x=0, y=0)
    a = Location(id="A", x=1, y=0)
    b = Location(id="B", x=1, y=2)
    # START->A = 1, A->B = 2, total = 3
    assert route_distance(start, [a, b]) == 3
