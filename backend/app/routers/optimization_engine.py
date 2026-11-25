from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from optimization.types import Location

from ..database import get_db
from ..deps import get_current_user
from ..filters import ReportFilters, run_filters
from ..models import User
from ..models.optimization_run import OptimizationRun
from ..providers.base import OrderRouteProvider
from ..providers.sqlalchemy import SqlAlchemyOrderRouteProvider
from ..schemas.optimization import (
    LocationSchema,
    OptimizationRunResponse,
    OptimizationSummaryResponse,
    PickLocationResponse,
    RouteOptimizeBatchItemResponse,
    RouteOptimizeBatchRequest,
    RouteOptimizeBatchResponse,
    RouteOptimizeByOrderRequest,
    RouteOptimizeRequest,
    RouteOptimizeResponse,
)
from ..services import report_service
from ..services.optimization_service import (
    get_pick_locations_for_order,
    is_native_compiled,
    optimize_batch_from_order_ids,
    optimize_from_order_id,
    optimize_from_request,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimization", tags=["optimization"])


def get_order_route_provider(db: Session = Depends(get_db)) -> OrderRouteProvider:
    """Provider Postgres (Sprint 06). Sobrescrevível nos testes."""
    return SqlAlchemyOrderRouteProvider(db)


class OptimizationRunRecorder:
    """Grava o histórico. Falha de persistência não interrompe a otimização."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def save(self, user: User, result, source: str, order_id: int | None = None) -> None:
        try:
            self.db.add(
                OptimizationRun(
                    user_id=user.id,
                    user_email=user.email,
                    executed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                    source=source,
                    order_id=order_id,
                    original_route=list(result.original_route),
                    nearest_neighbor_route=list(result.nearest_neighbor_route),
                    two_opt_route=list(result.two_opt_route),
                    distance_before=result.distance_before,
                    nearest_neighbor_distance=result.nearest_neighbor_distance,
                    two_opt_distance=result.two_opt_distance,
                    distance_after=result.distance_after,
                    distance_reduction=result.distance_reduction,
                    reduction_percent=result.reduction_percent,
                    execution_time_ms=result.execution_time_ms,
                    locations_count=result.locations_count,
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception(
                "Falha ao gravar optimization_runs (source=%s order_id=%s)",
                source,
                order_id,
            )


def get_run_recorder(db: Session = Depends(get_db)) -> OptimizationRunRecorder:
    return OptimizationRunRecorder(db)


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
    current_user: User = Depends(get_current_user),
    recorder: OptimizationRunRecorder = Depends(get_run_recorder),
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
    recorder.save(current_user, result, source="route")
    return _to_response(result)


@router.post("/route/by-order", response_model=RouteOptimizeResponse)
def optimize_route_by_order_endpoint(
    request: RouteOptimizeByOrderRequest,
    current_user: User = Depends(get_current_user),
    provider: OrderRouteProvider = Depends(get_order_route_provider),
    recorder: OptimizationRunRecorder = Depends(get_run_recorder),
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
    recorder.save(
        current_user,
        result,
        source="by-order",
        order_id=request.order_id,
    )
    return _to_response(result)


@router.post("/route/batch", response_model=RouteOptimizeBatchResponse)
def optimize_route_batch_endpoint(
    request: RouteOptimizeBatchRequest,
    current_user: User = Depends(get_current_user),
    provider: OrderRouteProvider = Depends(get_order_route_provider),
    recorder: OptimizationRunRecorder = Depends(get_run_recorder),
) -> RouteOptimizeBatchResponse:
    """Otimiza vários pedidos: baseline sequencial + ProcessPool; devolve S(p)/E(p)."""
    if len(set(request.order_ids)) != len(request.order_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="order_ids contém duplicados.",
        )
    try:
        order_ids, batch = optimize_batch_from_order_ids(
            request.order_ids,
            provider,
            start=_start_from_schema(request.start),
            workers=request.workers,
            repeats=request.repeats,
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

    items: list[RouteOptimizeBatchItemResponse] = []
    for order_id, result in zip(order_ids, batch.results):
        recorder.save(
            current_user,
            result,
            source="batch",
            order_id=order_id,
        )
        items.append(
            RouteOptimizeBatchItemResponse(
                order_id=order_id,
                result=_to_response(result),
            )
        )

    return RouteOptimizeBatchResponse(
        results=items,
        sequential_ms=batch.sequential_ms,
        parallel_ms=batch.parallel_ms,
        speedup=batch.speedup,
        efficiency=batch.efficiency,
        workers=batch.workers,
        orders_count=batch.jobs_count,
        native_compiled=is_native_compiled(),
    )


@router.get("/reports/summary", response_model=OptimizationSummaryResponse)
def optimization_summary(
    _: User = Depends(get_current_user),
    filters: ReportFilters = Depends(run_filters),
    db: Session = Depends(get_db),
) -> OptimizationSummaryResponse:
    """Redução média de distância (filtros opcionais: período e perfil)."""
    return OptimizationSummaryResponse(**report_service.optimization_summary(db, filters))


@router.get("/reports/picking", response_model=list[OptimizationRunResponse])
def optimization_picking_report(
    _: User = Depends(get_current_user),
    filters: ReportFilters = Depends(run_filters),
    db: Session = Depends(get_db),
) -> list[OptimizationRun]:
    """Relatório de picking: rotas, distâncias, tempo e quem executou."""
    return report_service.picking_runs(db, filters)


def _route_cell(route: list[str] | None) -> str:
    return " > ".join(route or [])


@router.get("/reports/picking.csv")
def optimization_picking_csv(
    _: User = Depends(get_current_user),
    filters: ReportFilters = Depends(run_filters),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Exporta o relatório de picking em CSV considerando os filtros aplicados."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "user_id",
            "user_email",
            "executed_at",
            "source",
            "order_id",
            "original_route",
            "nearest_neighbor_route",
            "two_opt_route",
            "distance_before",
            "nearest_neighbor_distance",
            "two_opt_distance",
            "distance_after",
            "distance_reduction",
            "reduction_percent",
            "execution_time_ms",
            "locations_count",
        ]
    )
    for run in report_service.picking_runs(db, filters):
        executed_at = run.executed_at.isoformat() if run.executed_at else ""
        writer.writerow(
            [
                run.id,
                run.user_id,
                run.user_email,
                executed_at,
                run.source,
                run.order_id if run.order_id is not None else "",
                _route_cell(run.original_route),
                _route_cell(run.nearest_neighbor_route),
                _route_cell(run.two_opt_route),
                run.distance_before,
                run.nearest_neighbor_distance,