from __future__ import annotations

from fastapi import APIRouter

from app.schemas.optimization import RouteOptimizeRequest, RouteOptimizeResponse
from app.services.optimization_service import optimize_from_request

router = APIRouter(prefix="/optimization", tags=["optimization"])


@router.post("/route", response_model=RouteOptimizeResponse)
def optimize_route_endpoint(request: RouteOptimizeRequest) -> RouteOptimizeResponse:
    """Otimiza a sequência de picking a partir de localizações explícitas.

    Endpoint principal da 1ª versão — não depende de PostgreSQL.
    """
    result = optimize_from_request(request)
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
