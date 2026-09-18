from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Location:
    """Posição visitável no armazém (coordenadas em grade)."""

    id: str
    x: float
    y: float


@dataclass(slots=True)
class OptimizationResult:
    """Resultado completo do pipeline NN + 2-opt com métricas calculadas."""

    original_route: list[str]
    nearest_neighbor_route: list[str]
    two_opt_route: list[str]
    distance_before: float
    nearest_neighbor_distance: float
    two_opt_distance: float
    distance_after: float
    distance_reduction: float
    reduction_percent: float
    execution_time_ms: float
    locations_count: int
    start: Location = field(repr=False)
