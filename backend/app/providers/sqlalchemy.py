"""Provider pedido → posições via Postgres (Sprint 06).

Não exige colunas ``x``/``y`` no banco: deriva a grade a partir de
aisle/rack/shelf/code (ver ``coords_from_warehouse_location``).
"""

from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from optimization.types import Location

from ..enums import OrderType
from ..models import Order, Stock
from .coords import coords_from_warehouse_location


class SqlAlchemyOrderRouteProvider:
    """Resolve posições de picking a partir de um pedido OUTBOUND no banco.

    Cadeia: Order → order_items → stock (qty > 0) → location → (code, x, y).
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_pick_locations(self, order_id: int) -> list[Location]:
        order = (
            self._db.query(Order)
            .options(joinedload(Order.items))
            .filter(Order.id == order_id)
            .first()
        )
        if order is None:
            raise KeyError(f"Pedido {order_id} não encontrado para picking")

        if order.type != OrderType.OUTBOUND:
            raise KeyError(
                f"Pedido {order_id} não é OUTBOUND (picking); tipo={order.type}"
            )

        items = sorted(order.items, key=lambda item: item.id)
        if not items:
            raise KeyError(
                f"Pedido {order_id} não possui itens com posição de picking"
            )

        result: list[Location] = []
        seen_codes: set[str] = set()

        for item in items:
            stock_rows = (
                self._db.query(Stock)
                .options(joinedload(Stock.location))
                .filter(
                    Stock.product_id == item.product_id,
                    Stock.quantity > 0,
                )
                .order_by(Stock.location_id)
                .all()
            )
            for stock in stock_rows:
                loc = stock.location
                if loc is None or not loc.is_active:
                    continue
                code = loc.code
                if code in seen_codes:
                    continue
                seen_codes.add(code)
                x, y = coords_from_warehouse_location(loc)
                result.append(Location(id=code, x=x, y=y))

        if not result:
            raise KeyError(
                f"Pedido {order_id} não possui itens com posição de picking"
            )

        return result
