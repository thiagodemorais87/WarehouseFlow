from __future__ import annotations

import csv
import io
from typing import Any, Iterable, Optional

from sqlalchemy import and_, case, exists, func, select
from sqlalchemy.orm import Session

from ..enums import OrderStatus, OrderType, TaskStatus, TaskType
from ..filters import ReportFilters
from ..models import (
    Location,
    Order,
    OrderItem,
    Product,
    Role,
    Stock,
    Task,
    User,
)
from ..models.optimization_run import OptimizationRun

EXPORT_LIMIT = 50_000  # teto de linhas por CSV
LOW_STOCK_LIST_SIZE = 10


def _val(x: Any) -> Any:
    return getattr(x, "value", x)


def _user_ids_with_role(f: ReportFilters):
    return (
        select(User.id)
        .join(Role, Role.id == User.role_id)
        .where(Role.name.in_(f.role_names))
    )


#  filtros

def apply_order_filters(query, f: ReportFilters):
    if f.start_dt:
        query = query.filter(Order.created_at >= f.start_dt)
    if f.end_dt:
        query = query.filter(Order.created_at < f.end_dt)
    if f.order_type:
        query = query.filter(Order.type == f.order_type)
    if f.order_status:
        query = query.filter(Order.status == f.order_status)
    if f.task_status or f.role:
        conds = [Task.order_id == Order.id]
        if f.task_status:
            conds.append(Task.status == f.task_status)
        if f.role:
            conds.append(Task.assigned_user_id.in_(_user_ids_with_role(f)))
        query = query.filter(exists().where(and_(*conds)))
    return query


def apply_task_filters(query, f: ReportFilters):
    if f.start_dt:
        query = query.filter(Task.created_at >= f.start_dt)
    if f.end_dt:
        query = query.filter(Task.created_at < f.end_dt)
    if f.task_status:
        query = query.filter(Task.status == f.task_status)
    if f.role:
        query = query.filter(Task.assigned_user_id.in_(_user_ids_with_role(f)))
    if f.user_id is not None:
        query = query.filter(Task.assigned_user_id == f.user_id)
    if f.order_type or f.order_status:
        sub = select(Order.id)
        if f.order_type:
            sub = sub.where(Order.type == f.order_type)
        if f.order_status:
            sub = sub.where(Order.status == f.order_status)
        query = query.filter(Task.order_id.in_(sub))
    return query


def apply_run_filters(query, f: ReportFilters):
    if f.start_dt:
        query = query.filter(OptimizationRun.executed_at >= f.start_dt)
    if f.end_dt:
        query = query.filter(OptimizationRun.executed_at < f.end_dt)
    if f.role:
        query = query.filter(OptimizationRun.user_id.in_(_user_ids_with_role(f)))
    if f.user_id is not None:
        query = query.filter(OptimizationRun.user_id == f.user_id)
    return query


#  otimização

def optimization_summary(db: Session, f: ReportFilters) -> dict:
    q = db.query(
        func.count(OptimizationRun.id),
        func.avg(OptimizationRun.distance_reduction),
        func.avg(OptimizationRun.reduction_percent),
    )
    runs_count, avg_reduction, avg_percent = apply_run_filters(q, f).one()
    return {
        "runs_count": int(runs_count or 0),
        "average_distance_reduction": float(avg_reduction or 0),
        "average_reduction_percent": float(avg_percent or 0),
    }


def picking_runs(db: Session, f: ReportFilters) -> list[OptimizationRun]:
    q = apply_run_filters(db.query(OptimizationRun), f)
    return q.order_by(OptimizationRun.executed_at.desc(), OptimizationRun.id.desc()).all()


#  dashboard

def _counts(db: Session, column, id_col, apply, f: ReportFilters, enum_cls) -> dict[str, int]:
    rows = apply(db.query(column, func.count(id_col)), f).group_by(column).all()
    found = {_val(k): int(v) for k, v in rows}
    return {e.value: found.get(e.value, 0) for e in enum_cls}


def build_dashboard(db: Session, f: ReportFilters, low_stock_threshold: int) -> dict:
    orders_by_status = _counts(db, Order.status, Order.id, apply_order_filters, f, OrderStatus)
    orders_by_type = _counts(db, Order.type, Order.id, apply_order_filters, f, OrderType)
    tasks_by_status = _counts(db, Task.status, Task.id, apply_task_filters, f, TaskStatus)
    tasks_by_type = _counts(db, Task.type, Task.id, apply_task_filters, f, TaskType)

    low_q = (
        db.query(Stock, Product, Location)
        .join(Product, Product.id == Stock.product_id)
        .join(Location, Location.id == Stock.location_id)
        .filter(Stock.quantity <= low_stock_threshold)
    )
    low_items = (
        low_q.order_by(Stock.quantity.asc(), Stock.id.asc()).limit(LOW_STOCK_LIST_SIZE).all()
    )
    total_units = db.query(func.coalesce(func.sum(Stock.quantity), 0)).scalar()
    products_total = db.query(func.count(Product.id)).scalar()

    return {
        "filters": f.as_dict(),
        "orders": {
            "total": sum(orders_by_status.values()),
            "by_status": orders_by_status,
            "by_type": orders_by_type,
        },
        "tasks": {
            "total": sum(tasks_by_status.values()),
            "open": tasks_by_status["PENDING"] + tasks_by_status["IN_PROGRESS"],
            "by_status": tasks_by_status,
            "by_type": tasks_by_type,
        },
        "stock": {
            "products_total": int(products_total or 0),
            "total_units": int(total_units or 0),
            "low_stock_threshold": low_stock_threshold,
            "low_stock_count": low_q.count(),
            "low_stock_items": [
                {
                    "stock_id": s.id,
                    "product_id": p.id,
                    "sku": p.sku,
                    "product_name": p.name,
                    "location_code": loc.code,
                    "quantity": s.quantity,
                }
                for s, p, loc in low_items
            ],
        },
        "optimization": optimization_summary(db, f),
    }


#  pedidos

def orders_report(
    db: Session, f: ReportFilters, skip: int = 0, limit: Optional[int] = None
) -> tuple[int, list[dict]]:
    base = apply_order_filters(db.query(Order), f)
    total = base.count()

    items_count = (
        select(func.count(OrderItem.id)).where(OrderItem.order_id == Order.id)
        .correlate(Order).scalar_subquery()
    )
    total_qty = (
        select(func.coalesce(func.sum(OrderItem.quantity), 0))
        .where(OrderItem.order_id == Order.id).correlate(Order).scalar_subquery()
    )
    tasks_count = (
        select(func.count(Task.id)).where(Task.order_id == Order.id)
        .correlate(Order).scalar_subquery()
    )
    q = apply_order_filters(
        db.query(Order, items_count, total_qty, tasks_count), f
    ).order_by(Order.created_at.desc(), Order.id.desc())
    q = q.offset(skip)
    if limit is not None:
        q = q.limit(limit)

    rows = [
        {
            "id": o.id,
            "type": _val(o.type),
            "status": _val(o.status),
            "created_at": o.created_at,
            "items_count": int(ic or 0),
            "total_quantity": int(tq or 0),
            "tasks_count": int(tc or 0),
        }
        for o, ic, tq, tc in q.all()
    ]
    return total, rows


#  movimentação de estoque

def _movements_base(db: Session, f: ReportFilters, product_id: Optional[int]):
    q = (
        db.query(
            OrderItem.id, Order.id, Order.type, Order.status, Order.created_at,
            Product.id, Product.sku, Product.name, OrderItem.quantity,
        )
        .select_from(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
    )
    q = apply_order_filters(q, f)
    if product_id is not None:
        q = q.filter(OrderItem.product_id == product_id)
    return q


def stock_movements_report(
    db: Session,
    f: ReportFilters,
    product_id: Optional[int] = None,
    skip: int = 0,
    limit: Optional[int] = None,
) -> dict:
    base = _movements_base(db, f, product_id)

    inbound = func.coalesce(
        func.sum(case((Order.type == OrderType.INBOUND, OrderItem.quantity), else_=0)), 0
    )
    outbound = func.coalesce(
        func.sum(case((Order.type == OrderType.OUTBOUND, OrderItem.quantity), else_=0)), 0
    )
    total, tot_in, tot_out = base.with_entities(func.count(OrderItem.id), inbound, outbound).one()

    q = base.order_by(Order.created_at.desc(), OrderItem.id.desc()).offset(skip)
    if limit is not None:
        q = q.limit(limit)

    items = []
    for item_id, order_id, otype, ostatus, created, pid, sku, pname, qty in q.all():
        mtype = _val(otype)
        items.append(
            {
                "order_id": order_id,
                "order_item_id": item_id,
                "movement_type": mtype,
                "order_status": _val(ostatus),
                "created_at": created,
                "product_id": pid,
                "sku": sku,
                "product_name": pname,
                "quantity": qty,
                "signed_quantity": qty if mtype == OrderType.INBOUND.value else -qty,
            }
        )
    return {
        "total": int(total or 0),
        "total_inbound": int(tot_in or 0),
        "total_outbound": int(tot_out or 0),
        "net_quantity": int(tot_in or 0) - int(tot_out or 0),
        "items": items,
    }


#  CSV

def _csv_safe(value: Any) -> Any:
    """Evita injeção de fórmulas ao abrir o CSV no Excel/Sheets."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def build_csv(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_csv_safe(c) for c in row])
    return "\ufeff" + buffer.getvalue()  # BOM: acentos corretos no Excel


ORDERS_CSV_HEADERS = ["id", "type", "status", "created_at", "items_count", "total_quantity", "tasks_count"]
MOVEMENTS_CSV_HEADERS = [
    "order_id", "order_item_id", "movement_type", "order_status", "created_at",
    "product_id", "sku", "product_name", "quantity", "signed_quantity",
]


def _iso(dt) -> str:
    return dt.isoformat() if dt else ""


def orders_csv(db: Session, f: ReportFilters) -> str:
    _, rows = orders_report(db, f, 0, EXPORT_LIMIT)
    return build_csv(
        ORDERS_CSV_HEADERS,
        ([r["id"], r["type"], r["status"], _iso(r["created_at"]), r["items_count"],
          r["total_quantity"], r["tasks_count"]] for r in rows),
    )


def stock_movements_csv(db: Session, f: ReportFilters, product_id: Optional[int]) -> str:
    data = stock_movements_report(db, f, product_id, 0, EXPORT_LIMIT)
    return build_csv(
        MOVEMENTS_CSV_HEADERS,
        ([r["order_id"], r["order_item_id"], r["movement_type"], r["order_status"],
          _iso(r["created_at"]), r["product_id"], r["sku"], r["product_name"],
          r["quantity"], r["signed_quantity"]] for r in data["items"]),
    )