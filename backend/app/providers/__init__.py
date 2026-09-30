"""Provedores pedido → posições de picking.

Sprint 05: MemoryOrderRouteProvider (catálogo acadêmico).
Sprint 06: SqlAlchemyOrderRouteProvider (Postgres + locations.x/y).
"""

from .base import OrderRouteProvider
from .memory import MemoryOrderRouteProvider, default_academic_catalog

__all__ = [
    "OrderRouteProvider",
    "MemoryOrderRouteProvider",
    "default_academic_catalog",
]
