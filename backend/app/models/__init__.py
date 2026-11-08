from sqlalchemy import (Column,Integer,String,Numeric,Boolean,ForeignKey,DateTime,JSON,Text,UniqueConstraint,CheckConstraint,Enum as SQLEnum,)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
from ..enums import OrderType, OrderStatus, TaskType, TaskStatus


def _in_list(column: str, enum_cls) -> str:
    """Gera `coluna IN ('A','B')` a partir de um Enum (CHECK no banco)."""
    return f"{column} IN ({', '.join(repr(e.value) for e in enum_cls)})"


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    role = relationship("Role", back_populates="users")
    tasks = relationship("Task", back_populates="assigned_user")

    @property
    def role_name(self) -> str | None:
        """Nome do perfil (ADMIN, GESTOR, OPERADOR) para JWT/RBAC."""
        return self.role.name if self.role else None


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("weight IS NULL OR weight >= 0", name="ck_products_weight_non_negative"),
        CheckConstraint("volume IS NULL OR volume >= 0", name="ck_products_volume_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    weight = Column(Numeric(10, 2), nullable=True)  # em kg
    volume = Column(Numeric(10, 2), nullable=True)  # em m3 ou cm3

    stocks = relationship("Stock", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")


class Warehouse(Base):
    __tablename__ = "warehouses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)

    locations = relationship("Location", back_populates="warehouse", cascade="all, delete-orphan", passive_deletes=True)


class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=True)
    code = Column(String(20), unique=True, nullable=False, index=True)  # Ex: A1-05-B
    aisle = Column(String(10), nullable=True)
    rack = Column(String(10), nullable=True)
    shelf = Column(String(10), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    warehouse = relationship("Warehouse", back_populates="locations")
    stocks = relationship("Stock", back_populates="location", cascade="all, delete-orphan")
    optimization_results = relationship("OptimizationResult", back_populates="suggested_location")


class Stock(Base):
    __tablename__ = "stock"
    __table_args__ = (
        UniqueConstraint("product_id", "location_id", name="uq_stock_product_location"),
        CheckConstraint("quantity >= 0", name="ck_stock_quantity_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    product = relationship("Product", back_populates="stocks")
    location = relationship("Location", back_populates="stocks")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(_in_list("type", OrderType), name="ck_orders_type"),
        CheckConstraint(_in_list("status", OrderStatus), name="ck_orders_status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    type = Column(SQLEnum(OrderType, native_enum=False), nullable=False)
    status = Column(
        SQLEnum(OrderStatus, native_enum=False),
        nullable=False,
        default=OrderStatus.PENDING,
    )
    created_at = Column(DateTime, server_default=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", passive_deletes=True)
    tasks = relationship("Task", back_populates="order", cascade="all, delete-orphan", passive_deletes=True)


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(_in_list("type", TaskType), name="ck_tasks_type"),
        CheckConstraint(_in_list("status", TaskStatus), name="ck_tasks_status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    type = Column(SQLEnum(TaskType, native_enum=False), nullable=False)
    status = Column(
        SQLEnum(TaskStatus, native_enum=False),
        nullable=False,
        default=TaskStatus.PENDING,
    )
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    assigned_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    order = relationship("Order", back_populates="tasks")
    assigned_user = relationship("User", back_populates="tasks")
    optimization_results = relationship("OptimizationResult", back_populates="task", cascade="all, delete-orphan", passive_deletes=True)


class OptimizationResult(Base):
    __tablename__ = "optimization_results"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    suggested_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    suggested_route = Column(JSON, nullable=True)
    score = Column(Numeric(10, 4), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    task = relationship("Task", back_populates="optimization_results")
    suggested_location = relationship("Location", back_populates="optimization_results")