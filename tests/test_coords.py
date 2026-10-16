"""Testes da derivação de coordenadas sem colunas x/y no banco."""

from app.providers.coords import coords_from_warehouse_location


def test_uses_code_when_aisle_missing():
    class _Loc:
        aisle = None
        rack = None
        shelf = None
        code = "C3-05-B"

    x, y = coords_from_warehouse_location(_Loc())
    assert x == 23.0  # C→20 + 3
    assert y == 6.0   # rack 5 + shelf B(+1)
