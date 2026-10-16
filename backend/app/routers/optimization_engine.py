from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from optimization.types import Location

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..providers.base import OrderRouteProvider
from ..providers.sqlalchemy import SqlAlchemyOrderRouteProvider
from ..schemas.optimization import (
    LocationSchema,
    PickLocationResponse,
    RouteOptimizeByOrderRequest,
    RouteOptimizeRequest,
    RouteOptimizeResponse,
)
from ..services.optimization_service import (
    get_pick_locations_for_order,
    optimize_from_order_id,
    optimize_from_request,
)

router = APIRouter(prefix="/optimization", tags=["optimization"])


def get_order_route_provider(db: Session = Depends(get_db)) -> OrderRouteProvider:
    """Provider Postgres (Sprint 06). Sobrescrevível nos testes."""
    return SqlAlchemyOrderRouteProvider(db)


def _to_response(result) -> RouteOptimizeResponse:
    return RouteOptimizeResponse(
        original_route=result.original_route,
        nearest_neighbor_route=result.nearest_neighbor_route,
        two_opt_route=result.two_opt_route,
        distance_before=result.distance_before,
        nearest_neighbor_distance=result.nearest_neighbor_distance,
        two_opt_distance=result.two_opt_distance,
        distance_after=result.distance_after,
        distance_reduction=result.distance_reduction,
        reduction_percent=result.reduction_percent,
        execution_time_ms=result.execution_time_ms,
        locations_count=result.locations_count,
    )


def _start_from_schema(schema: LocationSchema) -> Location:
    return Location(id=schema.id, x=schema.x, y=schema.y)


@router.post("/route", response_model=RouteOptimizeResponse)
def optimize_route_endpoint(
    request: RouteOptimizeRequest,
    _: User = Depends(get_current_user),
) -> RouteOptimizeResponse:
    """Otimiza a sequência de picking a partir de localizações explícitas.

    Endpoint principal consumido pelo frontend — não depende de PostgreSQL.
    Requer autenticação JWT.
    """
    try:
        result = optimize_from_request(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return _to_response(result)


@router.post("/route/by-order", response_model=RouteOptimizeResponse)
def optimize_route_by_order_endpoint(
    request: RouteOptimizeByOrderRequest,
    _: User = Depends(get_current_user),
    provider: OrderRouteProvider = Depends(get_order_route_provider),
) -> RouteOptimizeResponse:
    """Otimiza a rota a partir de um order_id OUTBOUND no Postgres."""
    try:
        result = optimize_from_order_id(
            request.order_id,
            provider,
            start=_start_from_schema(request.start),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return _to_response(result)


@router.get(
    "/orders/{order_id}/pick-locations",
    response_model=list[PickLocationResponse],
)
def list_pick_locations_for_order(
    order_id: int,
    _: User = Depends(get_current_user),
    provider: OrderRouteProvider = Depends(get_order_route_provider),
) -> list[PickLocationResponse]:
    """Lista posições de picking do pedido na ordem dos itens."""
    try:
        locations = get_pick_locations_for_order(order_id, provider)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return [
        PickLocationResponse(id=loc.id, x=loc.x, y=loc.y) for loc in locations
    ]
