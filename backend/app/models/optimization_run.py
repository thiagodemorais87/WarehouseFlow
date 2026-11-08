"""Histórico das execuções do motor de otimização (Sprint 07)."""

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String
from sqlalchemy.sql import func

from ..database import Base


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    user_email = Column(String(100), nullable=False)
    executed_at = Column(DateTime, nullable=False, server_default=func.now())
    source = Column(String(20), nullable=False)
    order_id = Column(Integer, nullable=True)
    original_route = Column(JSON, nullable=False)
    nearest_neighbor_route = Column(JSON, nullable=False)
    two_opt_route = Column(JSON, nullable=False)
    distance_before = Column(Float, nullable=False)
    nearest_neighbor_distance = Column(Float, nullable=False)
    two_opt_distance = Column(Float, nullable=False)
    distance_after = Column(Float, nullable=False)
    distance_reduction = Column(Float, nullable=False)
    reduction_percent = Column(Float, nullable=False)
    execution_time_ms = Column(Float, nullable=False)
    locations_count = Column(Integer, nullable=False)
