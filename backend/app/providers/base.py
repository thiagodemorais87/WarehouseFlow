from __future__ import annotations

from typing import Protocol

from optimization.types import Location


class OrderRouteProvider(Protocol):
    """Contrato futuro: pedido → posições de picking na ordem dos itens.

    A implementação real (SQLAlchemy/PostgreSQL) será feita por outro
    integrante. Este Protocol não acessa banco.
    """

    def get_pick_locations(self, order_id: int) -> list[Location]:
        """Retorna localizações na ordem original dos itens do pedido."""
        ...
