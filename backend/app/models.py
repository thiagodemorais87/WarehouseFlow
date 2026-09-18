from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, DateTime, JSON, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    role = relationship("Role", back_populates="users")
    tasks = relationship("Task", back_populates="assigned_user")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    weight = Column(Numeric(10, 2), nullable=True)  # em kg
    volume = Column(Numeric(10, 2), nullable=True)  # em m3 ou cm3

    stocks = relationship("Stock", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

class Warehouse(Base):
    __tablename__ = "warehouses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)

    locations = relationship("Location", back_populates="warehouse", cascade="all, delete-orphan")

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
    stocks = relationship("Stock", back_populates="location")
    optimization_results = relationship("OptimizationResult", back_populates="suggested_location")

class Stock(Base):
    __tablename__ = "stock"
    __table_args__ = (UniqueConstraint("product_id", "location_id", name="uq_stock_product_location"),)

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    product = relationship("Product", back_populates="stocks")
    location = relationship("Location", back_populates="stocks")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False)  # INBOUND (Recebimento) ou OUTBOUND (Expedição)
    status = Column(String(20), nullable=False, default="PENDING")
    created_at = Column(DateTime, default=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(30), nullable=False)  # PICKING, PUTAWAY, REPLENISHMENT
    status = Column(String(20), nullable=False, default="PENDING")
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    order = relationship("Order", back_populates="tasks")
    assigned_user = relationship("User", back_populates="tasks")
    optimization_results = relationship("OptimizationResult", back_populates="task", cascade="all, delete-orphan")

class OptimizationResult(Base):
    __tablename__ = "optimization_results"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    suggested_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    suggested_route = Column(JSON, nullable=True)  # Rota sugerida armazenada em formato JSON
    score = Column(Numeric(10, 4), nullable=True)  # Pontuação/Custo calculado pelo algoritmo
    created_at = Column(DateTime, default=func.now())

    task = relationship("Task", back_populates="optimization_results")
    suggested_location = relationship("Location", back_populates="optimization_results")