from optimization.distance import route_distance
from optimization.engine import optimize_route
from optimization.types import Location


START = Location(id="START", x=0, y=0)


def test_original_route_preserves_input_order():
    locations = [
        Location(id="C03", x=5, y=5),
        Location(id="A01", x=1, y=1),
        Location(id="D04", x=8, y=3),
        Location(id="B02", x=2, y=2),
    ]
    result = optimize_route(locations, start=START)
    assert result.original_route == ["START", "C03", "A01", "D04", "B02"]
    assert result.distance_before == route_distance(START, locations)


def test_metrics_are_calculated_not_hardcoded():
    locations = [
        Location(id="C03", x=5, y=5),
        Location(id="A01", x=1, y=1),
        Location(id="D04", x=8, y=3),
        Location(id="B02", x=2, y=2),
    ]
    result = optimize_route(locations, start=START)
    assert result.distance_reduction == result.distance_before - result.distance_after
    expected_pct = (result.distance_reduction / result.distance_before) * 100
    assert abs(result.reduction_percent - expected_pct) < 1e-9
    assert result.distance_after == result.two_opt_distance
    assert result.locations_count == 4
    assert result.execution_time_ms >= 0


def test_two_opt_distance_never_worse_than_nn():
    locations = [
        Location(id="C03", x=5, y=5),
        Location(id="A01", x=1, y=1),
        Location(id="B02", x=2, y=2),
        Location(id="D04", x=8, y=3),
    ]
    result = optimize_route(locations, start=START)
    assert result.two_opt_distance <= result.nearest_neighbor_distance


def test_zero_locations():
    result = optimize_route([], start=START)
    assert result.original_route == ["START"]
    assert result.nearest_neighbor_route == ["START"]
    assert result.two_opt_route == ["START"]
    assert result.distance_before == 0
    assert result.nearest_neighbor_distance == 0
    assert result.two_opt_distance == 0
    assert result.distance_reduction == 0
    assert result.reduction_percent == 0.0
    assert result.locations_count == 0


def test_single_location():
    locations = [Location(id="A01", x=3, y=4)]
    result = optimize_route(locations, start=START)
    assert result.original_route == ["START", "A01"]
    assert result.nearest_neighbor_route == ["START", "A01"]
    assert result.two_opt_route == ["START", "A01"]
    assert result.distance_before == 7
    assert result.nearest_neighbor_distance == 7
    assert result.two_opt_distance == 7
    assert result.locations_count == 1


def test_distance_before_zero_reduction_percent():
    # start coinciding with the only stop → before == 0
    start = Location(id="START", x=2, y=2)
    locations = [Location(id="A01", x=2, y=2)]
    result = optimize_route(locations, start=start)
    assert result.distance_before == 0
    assert result.reduction_percent == 0.0


def test_academic_demo_fixture_shows_real_reduction():
    """Ordem deliberadamente ruim: longe → perto → longe → perto."""
    locations = [
        Location(id="FAR1", x=10, y=0),
        Location(id="NEAR1", x=1, y=0),
        Location(id="FAR2", x=11, y=0),
        Location(id="NEAR2", x=2, y=0),
    ]
    result = optimize_route(locations, start=START)
    assert result.distance_before > result.distance_after
    assert result.distance_reduction > 0
    assert result.reduction_percent > 0
    assert result.two_opt_distance <= result.nearest_neighbor_distance


def test_optimization_may_not_beat_original():
    """Rota já ótima: reportar redução 0 (ou negativa se NN piorar) honestamente."""
    locations = [
        Location(id="A", x=1, y=0),
        Location(id="B", x=2, y=0),
        Location(id="C", x=3, y=0),
    ]
    result = optimize_route(locations, start=START)
    # Não forçar melhoria artificial
    assert result.distance_reduction == result.distance_before - result.distance_after
    assert result.two_opt_distance <= result.nearest_neighbor_distance
