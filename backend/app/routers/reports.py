from __future__ import annotations

from dataclasses import replace
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..filters import ReportFilters, report_filters
from ..models import User
from ..models.user import UserRole
from ..schemas.reports import (
    DashboardResponse,
    OrdersReportResponse,
    StockMovementsReportResponse,
)
from ..services import report_service

# Dashboard: qualquer autenticado. Relatórios e CSV: ADMIN e GESTOR.
router = APIRouter(prefix="/reports", tags=["Reports"])
_manager = Depends(require_role(UserRole.ADMIN, UserRole.GESTOR))


def _is_operator(user: User) -> bool:
    return (getattr(user, "role_name", None) or "").upper() in ("OPERADOR", "OPERATOR")


def _csv_response(text: str, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([text]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    low_stock_threshold: int = Query(10, ge=0, description="Estoque <= este valor é considerado baixo"),
    filters: ReportFilters = Depends(report_filters),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Indicadores gerais. OPERADOR vê tarefas e otimizações apenas as próprias
    (mesma regra de GET /tasks/); pedidos e estoque são globais."""
    if _is_operator(current_user):
        filters = replace(filters, user_id=current_user.id)
    return report_service.build_dashboard(db, filters, low_stock_threshold)


@router.get("/orders", response_model=OrdersReportResponse)
def orders_report(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    filters: ReportFilters = Depends(report_filters),
    db: Session = Depends(get_db),
    _: User = _manager,
):
    total, items = report_service.orders_report(db, filters, skip, limit)
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/orders.csv")
def orders_csv(
    filters: ReportFilters = Depends(report_filters),
    db: Session = Depends(get_db),
    _: User = _manager,
):
    """Exporta pedidos (com os mesmos filtros do relatório) em CSV."""
    return _csv_response(report_service.orders_csv(db, filters), "orders-report.csv")


@router.get("/stock-movements", response_model=StockMovementsReportResponse)
def stock_movements_report(
    product_id: Optional[int] = Query(None, description="Filtra por produto"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    filters: ReportFilters = Depends(report_filters),
    db: Session = Depends(get_db),
    _: User = _manager,
):
    """Movimentação de estoque (entradas INBOUND / saídas OUTBOUND) por item de pedido."""
    data = report_service.stock_movements_report(db, filters, product_id, skip, limit)
    return {**data, "skip": skip, "limit": limit}


@router.get("/stock-movements.csv")
def stock_movements_csv(
    product_id: Optional[int] = Query(None, description="Filtra por produto"),
    filters: ReportFilters = Depends(report_filters),
    db: Session = Depends(get_db),
    _: User = _manager,
):
    """Exporta a movimentação de estoque em CSV."""
    return _csv_response(
        report_service.stock_movements_csv(db, filters, product_id),
        "stock-movements-report.csv",
    )