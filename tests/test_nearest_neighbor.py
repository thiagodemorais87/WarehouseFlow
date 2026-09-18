from optimization.distance import route_distance
from optimization.nearest_neighbor import nearest_neighbor_route
from optimization.types import Location


def test_nearest_neighbor_empty():
    start = Location(id="START", x=0, y=0)
    assert nearest_neighbor_route(start, []) == []


def test_nearest_neighbor_single():
    start = Location(id="START", x=0, y=0)
    a = Location(id="A01", x=5, y=5)
    assert nearest_neighbor_route(start, [a]) == [a]


def test_nearest_neighbor_picks_closest_first():
    start = Location(id="START", x=0, y=0)
    far = Location(id="FAR", x=10, y=10)
    near = Location(id="NEAR", x=1, y=0)
    mid = Location(id="MID", x=3, y=0)
    result = nearest_neighbor_route(start, [far, mid, near])
    assert [loc.id for loc in result] == ["NEAR", "MID", "FAR"]


def test_nearest_neighbor_tie_break_by_id():
    start = Location(id="START", x=0, y=0)
    b = Location(id="B", x=1, y=0)
    a = Location(id="A", x=1, y=0)
    result = nearest_neighbor_route(start, [b, a])
    assert result[0].id == "A"


def test_nearest_neighbor_distance_is_computed():
    start = Location(id="START", x=0, y=0)
    locations = [
        Location(id="C", x=5, y=0),
        Location(id="A", x=1, y=0),
        Location(id="B", x=2, y=0),
    ]
    route = nearest_neighbor_route(start, locations)
    assert [loc.id for loc in route] == ["A", "B", "C"]
    assert route_distance(start, route) == 5
