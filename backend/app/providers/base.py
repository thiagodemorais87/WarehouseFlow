from __future__ import annotations

from typing import Protocol

from optimization.types import Location


class OrderRouteProvider(Protocol):
    """Contrato: pedido → posições de picking na ordem dos itens.

    Produção (S06): SqlAlchemyOrderRouteProvider (OUTBOUND → order_items
    → estoque → location; x,y derivados de aisle/rack/shelf).

    Implementações não devem acoplar o pacote ``optimization`` ao FastAPI.
    """

    def get_pick_locations(self, order_id: int) -> list[Location]:
        """Retorna localizações na ordem original dos itens do pedido.

        Raises:
            KeyError: se o pedido não existir no catálogo / banco.
        """
        ...
