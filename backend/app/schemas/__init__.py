from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from ..enums import OrderStatus, OrderType, TaskStatus, TaskType

# Teto de quantidade (cabe com folga no INTEGER do PostgreSQL: 2.147.483.647)
MAX_QUANTITY = 1_000_000

def _reject_null(*fields: str):
    """Em PUT, `{"campo": null}` é diferente de campo ausente: para colunas
    NOT NULL ele chegava ao banco e virava erro 500. Aqui vira 400."""
    @model_validator(mode="after")
    def _check(self):
        for name in fields:
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"O campo '{name}' não pode ser nulo.")
        return self
    return _check

# PRODUCT SCHEMAS

class ProductBase(BaseModel):
    sku: str = Field(..., max_length=50, examples=["PROD-001"])
    name: str = Field(..., max_length=150, examples=["Monitor LED 24\""])
    description: Optional[str] = None
    weight: Optional[Decimal] = Field(None, ge=0, description="Peso em kg")
    volume: Optional[Decimal] = Field(None, ge=0, description="Volume em m³")

class ProductCreate(ProductBase):
    model_config = ConfigDict(str_strip_whitespace=True)
    sku: str = Field(..., min_length=1, max_length=50, examples=["PROD-001"])
    name: str = Field(..., min_length=1, max_length=150, examples=["Monitor LED 24\""])

class ProductUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    weight: Optional[Decimal] = Field(None, ge=0)
    volume: Optional[Decimal] = Field(None, ge=0)
    _no_nulls = _reject_null("sku", "name")

class ProductResponse(ProductBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# OPTIMIZATION RESULT SCHEMAS

class OptimizationResultBase(BaseModel):
    task_id: int
    suggested_location_id: Optional[int] = None
    suggested_route: Optional[Dict[str, Any]] = Field(
        None,
        description="Representação em JSON da rota otimizada",
        examples=[{"steps": ["A1-01-A", "A1-01-B"], "total_distance_meters": 12.5}],
    )
    score: Optional[Decimal] = Field(
        None, description="Score/Custo calculado pelo algoritmo"
    )

class OptimizationResultCreate(OptimizationResultBase):
    pass

class OptimizationResultResponse(OptimizationResultBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# TASK SCHEMAS

class TaskBase(BaseModel):
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    order_id: int
    assigned_user_id: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None
    assigned_user_id: Optional[int] = None
    _no_nulls = _reject_null("type", "status")

class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    optimization_results: List[OptimizationResultResponse] = []

    model_config = ConfigDict(from_attributes=True)

# ORDER & ORDER ITEM SCHEMAS

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, description="Quantidade deve ser maior que zero")

class OrderItemCreate(OrderItemBase):
    quantity: int = Field(..., gt=0, le=MAX_QUANTITY, description=f"Quantidade entre 1 e {MAX_QUANTITY}")

class OrderItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0, le=MAX_QUANTITY, description=f"Nova quantidade entre 1 e {MAX_QUANTITY}")

class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    type: OrderType
    status: OrderStatus = OrderStatus.PENDING

class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(
        ..., min_length=1, description="O pedido deve ter ao menos 1 item"
    )

class OrderUpdate(BaseModel):
    type: Optional[OrderType] = None
    status: Optional[OrderStatus] = None
    _no_nulls = _reject_null("type", "status")

class OrderResponse(OrderBase):
    id: int
    created_at: datetime
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

# STOCK SCHEMAS

class StockBase(BaseModel):
    product_id: int
    location_id: int
    quantity: int = Field(..., ge=0, description="Quantidade em estoque")

class StockCreate(StockBase):
    quantity: int = Field(..., ge=0, le=MAX_QUANTITY, description=f"Quantidade em estoque (0 a {MAX_QUANTITY})")

class StockUpdate(BaseModel):
    quantity: int = Field(..., ge=0, le=MAX_QUANTITY)

class StockMovement(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantidade a movimentar")

class StockResponse(StockBase):
    id: int
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)

# USER & ROLE SCHEMAS

class RoleBase(BaseModel):
    name: str = Field(..., max_length=50, examples=["ADMIN", "GESTOR", "OPERADOR"])

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    name: str = Field(..., max_length=100)
    email: str = Field(..., max_length=100)
    role_id: Optional[int] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Senha do usuário")

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role_id: Optional[int] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    _no_nulls = _reject_null("name", "email", "password", "is_active")

class UserResponse(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime
    role: Optional[RoleResponse] = None

    model_config = ConfigDict(from_attributes=True)

# WAREHOUSE & LOCATION SCHEMAS

class WarehouseBase(BaseModel):
    name: str = Field(..., max_length=100)
    address: Optional[str] = None

class WarehouseCreate(WarehouseBase):
    name: str = Field(..., min_length=1, max_length=100)

class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = None
    _no_nulls = _reject_null("name")

class WarehouseResponse(WarehouseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class LocationBase(BaseModel):
    warehouse_id: int
    code: str = Field(..., max_length=20, examples=["A1-01-A"])
    aisle: Optional[str] = Field(None, max_length=10)
    rack: Optional[str] = Field(None, max_length=10)
    shelf: Optional[str] = Field(None, max_length=10)
    is_active: bool = True

class LocationCreate(LocationBase):
    model_config = ConfigDict(str_strip_whitespace=True)
    code: str = Field(..., min_length=1, max_length=20, examples=["A1-01-A"])

class LocationUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    aisle: Optional[str] = Field(None, max_length=10)
    rack: Optional[str] = Field(None, max_length=10)
    shelf: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None
    _no_nulls = _reject_null("code", "is_active")

class LocationResponse(LocationBase):
    id: int
    warehouse: Optional[WarehouseResponse] = None

    model_config = ConfigDict(from_attributes=True)