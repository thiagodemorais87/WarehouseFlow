from __future__ import annotations

from typing import Protocol

from optimization.types import Location


class OrderRouteProvider(Protocol):
    """Contrato: pedido → posições de picking na ordem dos itens.

    Sprint 05: MemoryOrderRouteProvider (catálogo em memória).
    Sprint 06: SqlAlchemyOrderRouteProvider (pedido OUTBOUND → order_items
    → produto → estoque → location com x,y).

    Implementações não devem acoplar o pacote ``optimization`` ao FastAPI.
    """

    def get_pick_locations(self, order_id: int) -> list[Location]:
        """Retorna localizações na ordem original dos itens do pedido.

        Raises:
            KeyError: se o pedido não existir no catálogo / banco.
        """
        ...
