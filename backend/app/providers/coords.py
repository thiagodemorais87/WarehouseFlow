"""Converte posição do armazém (aisle/rack/shelf/code) em coordenadas da grade.

Não altera o schema do banco: usa apenas campos já existentes em ``locations``.
A Pessoa responsável pelo banco pode, no futuro, expor ``x``/``y`` nativos;
enquanto isso o motor obtém a grade de forma determinística.
"""

from __future__ import annotations

from typing import Any


def coords_from_warehouse_location(loc: Any) -> tuple[float, float]:
    """Deriva (x, y) a partir de aisle, rack, shelf e code.

    Exemplos (seed típico):
    - A1-01-A → (1.0, 1.0)
    - A1-01-B → (1.0, 2.0)
    - B1-01-A → (11.0, 1.0)
    """
    aisle = (getattr(loc, "aisle", None) or "").strip().upper()
    rack = str(getattr(loc, "rack", None) or "").strip()
    shelf = (getattr(loc, "shelf", None) or "").strip().upper()
    code = (getattr(loc, "code", None) or "").strip().upper()
    parts = code.split("-") if code else []

    if not aisle and parts:
        aisle = parts[0]

    letter = next((c for c in aisle if c.isalpha()), "A")
    aisle_digits = "".join(c for c in aisle if c.isdigit()) or "0"
    rack_digits = "".join(c for c in rack if c.isdigit()) or "0"
    if rack_digits == "0" and len(parts) >= 2:
        rack_digits = "".join(c for c in parts[1] if c.isdigit()) or "0"

    if not shelf and len(parts) >= 3:
        shelf = parts[2]
    if not shelf:
        shelf = "A"

    shelf_letter = shelf[0] if shelf[0].isalpha() else "A"

    x = float((ord(letter) - ord("A")) * 10 + int(aisle_digits))
    y = float(int(rack_digits) + (ord(shelf_letter) - ord("A")))
    return x, y
