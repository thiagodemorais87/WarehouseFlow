from __future__ import annotations

from optimization.engine import optimize_route
from optimization.types import Location, OptimizationResult

from ..providers.base import OrderRouteProvider
from ..schemas.optimization import LocationSchema, RouteOptimizeRequest


def _to_location(schema: LocationSchema) -> Location:
    return Location(id=schema.id, x=schema.x, y=schema.y)


def optimize_from_request(request: RouteOptimizeRequest) -> OptimizationResult:
    """Converte o payload da API e executa o motor puro."""
    locations = [_to_location(loc) for loc in request.locations]
    start = _to_location(request.start)
    return optimize_route(locations, start=start)


def get_pick_locations_for_order(
    order_id: int,
    provider: OrderRouteProvider,
) -> list[Location]:
    """Obtém posições de picking na ordem dos itens via provider.

    Propaga KeyError se o pedido não existir no provider.
    """
    return provider.get_pick_locations(order_id)


def optimize_from_order_id(
    order_id: int,
    provider: OrderRouteProvider,
    start: Location | None = None,
) -> OptimizationResult:
    """Resolve posições pelo order_id e executa o mesmo motor de /route."""
    locations = get_pick_locations_for_order(order_id, provider)
    return optimize_route(locations, start=start)
