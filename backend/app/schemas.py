from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any, Dict, List
from datetime import datetime
from decimal import Decimal

# PRODUCT SCHEMAS

class ProductBase(BaseModel):
    sku: str = Field(..., max_length=50, examples=["PROD-001"])
    name: str = Field(..., max_length=150, examples=["Monitor LED 24\""])
    description: Optional[str] = None
    weight: Optional[Decimal] = Field(None, ge=0, description="Peso em kg")
    volume: Optional[Decimal] = Field(None, ge=0, description="Volume em m³")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    weight: Optional[Decimal] = Field(None, ge=0)
    volume: Optional[Decimal] = Field(None, ge=0)

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
        examples=[{"steps": ["A1-01-A", "A1-01-B"], "total_distance_meters": 12.5}]
    )
    score: Optional[Decimal] = Field(None, description="Score/Custo calculado pelo algoritmo")

class OptimizationResultCreate(OptimizationResultBase):
    pass

class OptimizationResultResponse(OptimizationResultBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# TASK SCHEMAS

class TaskBase(BaseModel):
    type: str = Field(..., description="Tipo da tarefa: PICKING, PUTAWAY ou REPLENISHMENT")
    status: str = Field("PENDING", description="Status: PENDING, IN_PROGRESS, COMPLETED")
    order_id: int
    assigned_user_id: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    type: Optional[str] = None
    status: Optional[str] = None
    assigned_user_id: Optional[int] = None

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
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    type: str = Field(..., description="INBOUND para recebimento, OUTBOUND para expedição")
    status: str = Field("PENDING", description="PENDING, PROCESSING, COMPLETED, CANCELLED")

class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_length=1, description="O pedido deve ter ao menos 1 item")

class OrderUpdate(BaseModel):
    type: Optional[str] = None
    status: Optional[str] = None

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
    pass

class StockUpdate(BaseModel):
    quantity: int = Field(..., ge=0)

class StockResponse(StockBase):
    id: int
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)

# USER & ROLE SCHEMAS

class RoleBase(BaseModel):
    name: str = Field(..., max_length=50, examples=["ADMIN", "OPERATOR"])

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

class UserResponse(UserBase):
    id: int
    created_at: datetime
    role: Optional[RoleResponse] = None

    model_config = ConfigDict(from_attributes=True)

# WAREHOUSE & LOCATION SCHEMAS

class WarehouseBase(BaseModel):
    name: str = Field(..., max_length=100)
    address: Optional[str] = None

class WarehouseCreate(WarehouseBase):
    pass

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
    pass

class LocationUpdate(BaseModel):
    code: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    shelf: Optional[str] = None
    is_active: Optional[bool] = None

class LocationResponse(LocationBase):
    id: int
    warehouse: Optional[WarehouseResponse] = None

    model_config = ConfigDict(from_attributes=True)