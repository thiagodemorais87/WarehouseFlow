from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LocationSchema(BaseModel):
    id: str = Field(..., description="Identificador da posição (ex.: A01, FAR1).")
    x: float = Field(..., description="Coordenada X na grade do armazém.")
    y: float = Field(..., description="Coordenada Y na grade do armazém.")


class RouteOptimizeRequest(BaseModel):
    locations: list[LocationSchema] = Field(
        default_factory=list,
        description="Posições a visitar na ordem original do pedido/itens.",
    )
    start: LocationSchema = Field(
        default_factory=lambda: LocationSchema(id="START", x=0, y=0),
        description="Ponto de partida do picking. Default: START em (0, 0).",
    )


class RouteOptimizeByOrderRequest(BaseModel):
    order_id: int = Field(
        ...,
        ge=1,
        description="ID do pedido OUTBOUND cujas posições serão otimizadas.",
    )
    start: LocationSchema = Field(
        default_factory=lambda: LocationSchema(id="START", x=0, y=0),
        description="Ponto de partida do picking. Default: START em (0, 0).",
    )


class PickLocationResponse(BaseModel):
    id: str = Field(..., description="Identificador da posição (ex.: A01).")
    x: float = Field(..., description="Coordenada X na grade do armazém.")
    y: float = Field(..., description="Coordenada Y na grade do armazém.")


class RouteOptimizeResponse(BaseModel):
    original_route: list[str] = Field(
        ...,
        description="Rota antes da otimização: START + ids na ordem de entrada.",
    )
    nearest_neighbor_route: list[str] = Field(
        ...,
        description="Rota após a heurística Nearest Neighbor.",
    )
    two_opt_route: list[str] = Field(
        ...,
        description="Rota sugerida após 2-opt — usar como rota principal na UI.",
    )
    distance_before: float = Field(
        ...,
        description="Distância Manhattan da rota original.",
    )
    nearest_neighbor_distance: float = Field(
        ...,
        description="Distância Manhattan após Nearest Neighbor.",
    )
    two_opt_distance: float = Field(
        ...,
        description="Distância Manhattan após 2-opt.",
    )
    distance_after: float = Field(
        ...,
        description="Alias de two_opt_distance (distância final sugerida).",
    )
    distance_reduction: float = Field(
        ...,
        description="distance_before - distance_after (pode ser <= 0).",
    )
    reduction_percent: float = Field(
        ...,
        description="Redução percentual; 0 se distance_before == 0.",
    )
    execution_time_ms: float = Field(
        ...,
        description="Tempo de execução do algoritmo em milissegundos.",
    )
    locations_count: int = Field(
        ...,
        description="Quantidade de posições em locations (sem contar START).",
    )


class OptimizationSummaryResponse(BaseModel):
    runs_count: int = Field(..., description="Quantidade de execuções gravadas.")
    average_distance_reduction: float = Field(
        ...,
        description="Média de distance_reduction. 0 se não houver execuções.",
    )
    average_reduction_percent: float = Field(
        ...,
        description="Média de reduction_percent. 0 se não houver execuções.",
    )


class OptimizationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_email: str
    executed_at: datetime
    source: str
    order_id: int | None = None
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
