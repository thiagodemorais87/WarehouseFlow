from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .optimization import OptimizationSummaryResponse


class OrderReportRow(BaseModel):
    id: int
    type: str
    status: str
    created_at: Optional[datetime] = None
    items_count: int
    total_quantity: int
    tasks_count: int


class OrdersReportResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[OrderReportRow]


class StockMovementRow(BaseModel):
    order_id: int
    order_item_id: int
    movement_type: str  # INBOUND (entrada) | OUTBOUND (saída)
    order_status: str
    created_at: Optional[datetime] = None
    product_id: int
    sku: str
    product_name: str
    quantity: int
    signed_quantity: int  # + entrada, - saída


class StockMovementsReportResponse(BaseModel):
    total: int
    total_inbound: int
    total_outbound: int
    net_quantity: int
    skip: int
    limit: int
    items: list[StockMovementRow]


class LowStockItem(BaseModel):
    stock_id: int
    product_id: int
    sku: str
    product_name: str
    location_code: str
    quantity: int


class DashboardOrders(BaseModel):
    total: int
    by_status: dict[str, int]
    by_type: dict[str, int]


class DashboardTasks(BaseModel):
    total: int
    open: int  # PENDING + IN_PROGRESS
    by_status: dict[str, int]
    by_type: dict[str, int]


class DashboardStock(BaseModel):
    """Posição atual (não depende do período)."""

    products_total: int
    total_units: int
    low_stock_threshold: int
    low_stock_count: int
    low_stock_items: list[LowStockItem]


class DashboardResponse(BaseModel):
    filters: dict[str, Optional[str]]
    orders: DashboardOrders
    tasks: DashboardTasks
    stock: DashboardStock
    optimization: OptimizationSummaryResponse