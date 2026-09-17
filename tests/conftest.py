"""Fixtures determinísticas compartilhadas."""

import pytest

from optimization.types import Location


@pytest.fixture
def start() -> Location:
    return Location(id="START", x=0, y=0)


@pytest.fixture
def academic_demo_locations() -> list[Location]:
    """Ordem original deliberadamente ineficiente para demonstração acadêmica."""
    return [
        Location(id="FAR1", x=10, y=0),
        Location(id="NEAR1", x=1, y=0),
        Location(id="FAR2", x=11, y=0),
        Location(id="NEAR2", x=2, y=0),
    ]


@pytest.fixture
def sample_warehouse_locations() -> list[Location]:
    return [
        Location(id="A01", x=1, y=1),
        Location(id="C03", x=5, y=5),
        Location(id="B02", x=2, y=2),
        Location(id="D04", x=8, y=3),
    ]
