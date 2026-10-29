from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional

from fastapi import HTTPException, Query, status

from .enums import OrderStatus, OrderType, TaskStatus
from .models.user import UserRole

_ROLE_DB_NAMES: dict[UserRole, set[str]] = {
    UserRole.ADMIN: {"ADMIN"},
    UserRole.GESTOR: {"GESTOR", "MANAGER"},
    UserRole.OPERADOR: {"OPERADOR", "OPERATOR"},
}


@dataclass(frozen=True)
class ReportFilters:
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    order_type: Optional[OrderType] = None
    order_status: Optional[OrderStatus] = None
    task_status: Optional[TaskStatus] = None
    role: Optional[UserRole] = None

    @property
    def start_dt(self) -> Optional[datetime]:
        return datetime.combine(self.date_from, time.min) if self.date_from else None

    @property
    def end_dt(self) -> Optional[datetime]:
        if not self.date_to:
            return None
        return datetime.combine(self.date_to + timedelta(days=1), time.min)

    @property
    def role_names(self) -> set[str]:
        return _ROLE_DB_NAMES[self.role] if self.role else set()

    def as_dict(self) -> dict[str, Optional[str]]:
        return {
            "date_from": self.date_from.isoformat() if self.date_from else None,
            "date_to": self.date_to.isoformat() if self.date_to else None,
            "type": self.order_type.value if self.order_type else None,
            "status": self.order_status.value if self.order_status else None,
            "task_status": self.task_status.value if self.task_status else None,
            "role": self.role.value if self.role else None,
        }


def _check_period(date_from, date_to) -> None:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Período inválido: 'date_from' deve ser anterior ou igual a 'date_to'.",
        )


def report_filters(
    date_from: Optional[date] = Query(None, description="Início do período (AAAA-MM-DD, inclusivo)"),
    date_to: Optional[date] = Query(None, description="Fim do período (AAAA-MM-DD, inclusivo)"),
    order_type: Optional[OrderType] = Query(None, alias="type", description="INBOUND ou OUTBOUND"),
    order_status: Optional[OrderStatus] = Query(None, alias="status", description="Status do pedido"),
    task_status: Optional[TaskStatus] = Query(None, description="Status da tarefa"),
    role: Optional[UserRole] = Query(None, description="Perfil do usuário responsável"),
) -> ReportFilters:
    _check_period(date_from, date_to)
    return ReportFilters(date_from, date_to, order_type, order_status, task_status, role)


def run_filters(
    date_from: Optional[date] = Query(None, description="Início do período (AAAA-MM-DD, inclusivo)"),
    date_to: Optional[date] = Query(None, description="Fim do período (AAAA-MM-DD, inclusivo)"),
    role: Optional[UserRole] = Query(None, description="Perfil de quem executou a otimização"),
) -> ReportFilters:
    _check_period(date_from, date_to)
    return ReportFilters(date_from=date_from, date_to=date_to, role=role)