from __future__ import annotations

from optimization.types import Location


class MemoryOrderRouteProvider:
    """Provider em memória apenas para demonstrar o contrato futuro.

    NÃO é o banco real. Útil em testes de integração da API quando
    `order_id` estiver disponível.
    """

    def __init__(self, catalog: dict[int, list[Location]] | None = None) -> None:
        self._catalog = catalog or {}

    def get_pick_locations(self, order_id: int) -> list[Location]:
        if order_id not in self._catalog:
            raise KeyError(f"Pedido {order_id} não encontrado no provider em memória")
        return list(self._catalog[order_id])
