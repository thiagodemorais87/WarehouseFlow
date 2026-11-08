"""Provedores pedido → posições de picking.

Sprint 05: MemoryOrderRouteProvider (catálogo acadêmico / testes).
Sprint 06: SqlAlchemyOrderRouteProvider (Postgres; grade derivada de aisle/rack/shelf).
"""

from .base import OrderRouteProvider
from .coords import coords_from_warehouse_location
from .memory import MemoryOrderRouteProvider, default_academic_catalog
from .sqlalchemy import SqlAlchemyOrderRouteProvider

__all__ = [
    "OrderRouteProvider",
    "MemoryOrderRouteProvider",
    "SqlAlchemyOrderRouteProvider",
    "coords_from_warehouse_location",
    "default_academic_catalog",
]
