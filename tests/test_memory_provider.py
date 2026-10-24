"""Testes do MemoryOrderRouteProvider (ponte order_id → posições)."""

import pytest

from app.providers.memory import MemoryOrderRouteProvider, default_academic_catalog
from optimization.types import Location


def test_default_catalog_contains_academic_orders():
    provider = MemoryOrderRouteProvider()
    locs = provider.get_pick_locations(1)
    assert [loc.id for loc in locs] == ["FAR1", "NEAR1", "FAR2", "NEAR2"]
    locs2 = provider.get_pick_locations(2)
    assert [loc.id for loc in locs2] == ["A01", "C03", "B02", "D04"]


def test_default_catalog_returns_defensive_copy():
    provider = MemoryOrderRouteProvider()
    locs = provider.get_pick_locations(1)
    locs.append(Location(id="HACK", x=99, y=99))
    again = provider.get_pick_locations(1)
    assert [loc.id for loc in again] == ["FAR1", "NEAR1", "FAR2", "NEAR2"]


def test_missing_order_raises_key_error():
    provider = MemoryOrderRouteProvider()
    with pytest.raises(KeyError, match="Pedido 999"):
        provider.get_pick_locations(999)


def test_custom_catalog_overrides_default():
    catalog = {10: [Location(id="X1", x=0, y=1)]}
    provider = MemoryOrderRouteProvider(catalog=catalog)
    assert provider.get_pick_locations(10)[0].id == "X1"
    with pytest.raises(KeyError):
        provider.get_pick_locations(1)


def test_default_academic_catalog_is_independent_copy():
    a = default_academic_catalog()
    b = default_academic_catalog()
    a[1].clear()
    assert len(b[1]) == 4
