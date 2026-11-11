"""Testes do SqlAlchemyOrderRouteProvider com SQLite em memória.

Não depende de colunas x/y no schema — coordenadas vêm de aisle/rack/shelf.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db
from app.deps import get_current_user
from app.enums import OrderStatus, OrderType
from app.models import Location, Order, OrderItem, Product, Stock, Warehouse
from app.providers.coords import coords_from_warehouse_location
from app.providers.sqlalchemy import SqlAlchemyOrderRouteProvider
from app.routers.optimization_engine import router as optimization_router
from app.services.optimization_service import optimize_from_order_id


class _FakeUser:
    id = 1
    email = "test@warehouseflow.com"
    is_active = True
    role_name = "ADMIN"


@pytest.fixture()
def db() -> Session:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        session.add(Warehouse(id=1, name="Central", address="Recife"))
        session.flush()

        session.add_all(
            [
                Location(
                    id=1, warehouse_id=1, code="A1-01-A", aisle="A1",
                    rack="01", shelf="A", is_active=True,
                ),
                Location(
                    id=2, warehouse_id=1, code="A1-01-B", aisle="A1",
                    rack="01", shelf="B", is_active=True,
                ),
                Location(
                    id=3, warehouse_id=1, code="A1-02-A", aisle="A1",
                    rack="02", shelf="A", is_active=True,
                ),
            ]
        )
        session.add_all(
            [
                Product(id=1, sku="P1", name="Monitor"),
                Product(id=2, sku="P2", name="Teclado"),
                Product(id=3, sku="P3", name="Cabo"),
            ]
        )
        session.flush()
        session.add_all(
            [
                Stock(product_id=1, location_id=1, quantity=15),
                Stock(product_id=2, location_id=2, quantity=40),
                Stock(product_id=3, location_id=3, quantity=100),
            ]
        )
        session.add_all(
            [
                Order(id=1, type=OrderType.OUTBOUND, status=OrderStatus.PENDING),
                Order(id=2, type=OrderType.INBOUND, status=OrderStatus.COMPLETED),
                Order(id=3, type=OrderType.OUTBOUND, status=OrderStatus.PENDING),
            ]
        )
        session.flush()
        session.add_all(
            [
                OrderItem(order_id=1, product_id=1, quantity=2),
                OrderItem(order_id=1, product_id=2, quantity=1),
                OrderItem(order_id=2, product_id=3, quantity=50),
            ]
        )
        session.commit()
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_coords_from_aisle_rack_shelf():
    class _Loc:
        aisle = "A1"
        rack = "01"
        shelf = "A"
        code = "A1-01-A"

    assert coords_from_warehouse_location(_Loc()) == (1.0, 1.0)

    class _LocB:
        aisle = "A1"
        rack = "01"
        shelf = "B"
        code = "A1-01-B"

    assert coords_from_warehouse_location(_LocB()) == (1.0, 2.0)

    class _LocFar:
        aisle = "B1"
        rack = "01"
        shelf = "A"
        code = "B1-01-A"

    assert coords_from_warehouse_location(_LocFar()) == (11.0, 1.0)


def test_outbound_resolves_locations_in_item_order(db: Session):
    provider = SqlAlchemyOrderRouteProvider(db)
    locs = provider.get_pick_locations(1)
    assert [loc.id for loc in locs] == ["A1-01-A", "A1-01-B"]
    assert locs[0].x == 1.0 and locs[0].y == 1.0
    assert locs[1].x == 1.0 and locs[1].y == 2.0


def test_inbound_rejected(db: Session):
    provider = SqlAlchemyOrderRouteProvider(db)
    with pytest.raises(KeyError, match="OUTBOUND"):
        provider.get_pick_locations(2)


def test_order_not_found(db: Session):
    provider = SqlAlchemyOrderRouteProvider(db)
    with pytest.raises(KeyError, match="999"):
        provider.get_pick_locations(999)


def test_empty_order_no_positions(db: Session):
    provider = SqlAlchemyOrderRouteProvider(db)
    with pytest.raises(KeyError, match="não possui itens"):
        provider.get_pick_locations(3)


def test_dedupe_keeps_first_occurrence(db: Session):
    db.add(OrderItem(order_id=1, product_id=1, quantity=1))
    db.commit()
    provider = SqlAlchemyOrderRouteProvider(db)
    codes = [loc.id for loc in provider.get_pick_locations(1)]
    assert codes.count("A1-01-A") == 1
    assert codes == ["A1-01-A", "A1-01-B"]


def test_optimize_from_order_id_runs_motor(db: Session):
    provider = SqlAlchemyOrderRouteProvider(db)
    result = optimize_from_order_id(1, provider)
    assert result.original_route == ["START", "A1-01-A", "A1-01-B"]
    assert result.locations_count == 2
    assert result.two_opt_distance <= result.nearest_neighbor_distance
    assert result.execution_time_ms >= 0


def test_api_by_order_with_sqlalchemy_provider(db: Session):
    app = FastAPI()
    app.include_router(optimization_router)
    app.dependency_overrides[get_current_user] = lambda: _FakeUser()

    def _override_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app)

    response = client.post(
        "/optimization/route/by-order",
        json={"order_id": 1, "start": {"id": "START", "x": 0, "y": 0}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["original_route"] == ["START", "A1-01-A", "A1-01-B"]
    assert "two_opt_route" in data
    assert data["locations_count"] == 2

    pick = client.get("/optimization/orders/1/pick-locations")
    assert pick.status_code == 200
    assert [item["id"] for item in pick.json()] == ["A1-01-A", "A1-01-B"]

    missing = client.post("/optimization/route/by-order", json={"order_id": 999})
    assert missing.status_code == 404
    assert "999" in missing.json()["detail"]

    empty = client.post("/optimization/route/by-order", json={"order_id": 3})
    assert empty.status_code == 404
    assert "não possui itens" in empty.json()["detail"].lower()
