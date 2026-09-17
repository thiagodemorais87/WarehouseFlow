from __future__ import annotations

from pydantic import BaseModel, Field


class LocationSchema(BaseModel):
    id: str
    x: float
    y: float


class RouteOptimizeRequest(BaseModel):
    locations: list[LocationSchema] = Field(default_factory=list)
    start: LocationSchema = Field(
        default_factory=lambda: LocationSchema(id="START", x=0, y=0)
    )


class RouteOptimizeResponse(BaseModel):
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
