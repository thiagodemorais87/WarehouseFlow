from __future__ import annotations

from optimization.engine import optimize_route
from optimization.types import Location, OptimizationResult

from ..schemas.optimization import LocationSchema, RouteOptimizeRequest


def _to_location(schema: LocationSchema) -> Location:
    return Location(id=schema.id, x=schema.x, y=schema.y)


def optimize_from_request(request: RouteOptimizeRequest) -> OptimizationResult:
    """Converte o payload da API e executa o motor puro."""
    locations = [_to_location(loc) for loc in request.locations]
    start = _to_location(request.start)
    return optimize_route(locations, start=start)
