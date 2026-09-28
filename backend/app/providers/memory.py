from __future__ import annotations

from optimization.types import Location

# Catálogo acadêmico default (Sprint 05): ponte para by-order sem Postgres.
# order_id=1 = fixture FAR/NEAR usada nos testes do motor.
# Na Sprint 06 será substituído por SqlAlchemyOrderRouteProvider.
_DEFAULT_ACADEMIC_CATALOG: dict[int, list[Location]] = {
    1: [
        Location(id="FAR1", x=10, y=0),
        Location(id="NEAR1", x=1, y=0),
        Location(id="FAR2", x=11, y=0),
        Location(id="NEAR2", x=2, y=0),
    ],
    2: [
        Location(id="A01", x=1, y=1),
        Location(id="C03", x=5, y=5),
        Location(id="B02", x=2, y=2),
        Location(id="D04", x=8, y=3),
    ],
}


def default_academic_catalog() -> dict[int, list[Location]]:
    """Cópia do catálogo acadêmico (evita mutação compartilhada)."""
    return {
        order_id: [Location(id=loc.id, x=loc.x, y=loc.y) for loc in locs]
        for order_id, locs in _DEFAULT_ACADEMIC_CATALOG.items()
    }


class MemoryOrderRouteProvider:
    """Provider em memória para demonstrar o contrato pedido → posições.

    NÃO é o banco real. Útil em testes e no endpoint by-order da Sprint 05
    até existir SqlAlchemyOrderRouteProvider (Sprint 06).
    """

    def __init__(self, catalog: dict[int, list[Location]] | None = None) -> None:
        if catalog is None:
            self._catalog = default_academic_catalog()
        else:
            self._catalog = {
                order_id: list(locs) for order_id, locs in catalog.items()
            }

    def get_pick_locations(self, order_id: int) -> list[Location]:
        if order_id not in self._catalog:
            raise KeyError(
                f"Pedido {order_id} não encontrado no catálogo de picking"
            )
        return list(self._catalog[order_id])
