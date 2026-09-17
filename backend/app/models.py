from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
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
    role_id = Column(Integer, ForeignKey("roles.id"))
    created_at = Column(DateTime, default=func.now())

    role = relationship("Role", back_populates="users")
    tasks = relationship("Task", back_populates="assigned_user")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(String)
    weight = Column(Float)
    volume = Column(Float)

    stocks = relationship("Stock", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # Ex: "CORREDOR-01-PRAT-02"
    zone = Column(String(50))                                          # Ex: "Recebimento", "Pick", "Pulmão"
    max_capacity = Column(Float)

    stocks = relationship("Stock", back_populates="location")
    tasks = relationship("Task", back_populates="location")

class Stock(Base):
    __tablename__ = "stock"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)

    product = relationship("Product", back_populates="stocks")
    location = relationship("Location", back_populates="stocks")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(50), default="pending")  # pendente, escolhido, empacotado, enviado, cancelado
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), nullable=False)  # Ex: "escolha", "armazenagem", "inventário"
    status = Column(String(50), default="pending")  # pending, em progresso, completado, cancelado
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)

    assigned_user = relationship("User", back_populates="tasks")
    order = relationship("Order", back_populates="tasks")
    location = relationship("Location", back_populates="tasks")