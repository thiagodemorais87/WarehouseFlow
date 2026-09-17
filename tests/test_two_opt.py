from optimization.distance import route_distance
from optimization.two_opt import two_opt_improve
from optimization.types import Location


def test_two_opt_empty():
    start = Location(id="START", x=0, y=0)
    assert two_opt_improve(start, []) == []


def test_two_opt_single():
    start = Location(id="START", x=0, y=0)
    a = Location(id="A", x=1, y=1)
    assert two_opt_improve(start, [a]) == [a]


def test_two_opt_never_worsens_route():
    start = Location(id="START", x=0, y=0)
    # Crossed order that 2-opt can untangle on a line-ish layout
    route = [
        Location(id="A", x=0, y=1),
        Location(id="C", x=0, y=3),
        Location(id="B", x=0, y=2),
        Location(id="D", x=0, y=4),
    ]
    before = route_distance(start, route)
    improved = two_opt_improve(start, route)
    after = route_distance(start, improved)
    assert after <= before
    assert {loc.id for loc in improved} == {loc.id for loc in route}
    assert len(improved) == len(route)


def test_two_opt_improves_crossed_path():
    start = Location(id="START", x=0, y=0)
    # Visit far, then near-start, then far again — NN would avoid this;
    # 2-opt should reduce crossings when given a bad seed.
    bad = [
        Location(id="A", x=1, y=0),
        Location(id="C", x=10, y=0),
        Location(id="B", x=2, y=0),
        Location(id="D", x=11, y=0),
    ]
    before = route_distance(start, bad)
    improved = two_opt_improve(start, bad)
    after = route_distance(start, improved)
    assert after < before
