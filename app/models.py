from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class UniverseMetadata(BaseModel):
    system_name: str
    speed_of_light_kms: float
    max_void_hop_distance_km: float
    coordinate_scale_unit_km: float
    tower_processing_delay_ms: float
    fiber_speed_fraction: float

    @field_validator(
        "speed_of_light_kms",
        "max_void_hop_distance_km",
        "coordinate_scale_unit_km",
        "tower_processing_delay_ms",
        "fiber_speed_fraction",
    )
    @classmethod
    def positive_constants(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("metadata constants must be positive")
        return value


class PlanetNode(BaseModel):
    id: str
    codex: int
    x: float
    y: float
    radius_km: float
    active_towers: int
    atmosphere_thickness_km: float
    refraction_index: float

    @field_validator("codex")
    @classmethod
    def codex_supported(cls, value: int) -> int:
        if value < 2:
            raise ValueError("codex must be at least 2")
        if value > 36:
            raise ValueError("codex values above 36 are not supported by 0-9/A-Z digits")
        return value

    @field_validator("active_towers")
    @classmethod
    def enough_towers(cls, value: int) -> int:
        if value < 4:
            raise ValueError("active_towers must be at least 4")
        return value

    @field_validator("radius_km", "atmosphere_thickness_km", "refraction_index")
    @classmethod
    def positive_planet_values(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("radius, atmosphere thickness, and refraction index must be positive")
        return value


class UniverseConfig(BaseModel):
    universe_metadata: UniverseMetadata
    nodes: list[PlanetNode] = Field(min_length=1)

    @model_validator(mode="after")
    def no_duplicate_planet_ids(self) -> "UniverseConfig":
        ids = [node.id for node in self.nodes]
        duplicates = sorted({planet_id for planet_id in ids if ids.count(planet_id) > 1})
        if duplicates:
            raise ValueError(f"duplicate planet IDs: {', '.join(duplicates)}")
        return self


class LoadUniverseRequest(BaseModel):
    path: Optional[str] = None


class RouteRequest(BaseModel):
    origin_id: str
    destination_id: str
    origin_tower: Optional[int] = None
    destination_tower: Optional[int] = None


class PacketSendRequest(RouteRequest):
    payload: str


class NodeFailureRequest(BaseModel):
    node_id: str


class LinkFailureRequest(BaseModel):
    from_id: str
    to_id: str
    bidirectional: bool = True


class ChaosDemoRequest(PacketSendRequest):
    fail_node_id: Optional[str] = None
    fail_from_id: Optional[str] = None
    fail_to_id: Optional[str] = None
    bidirectional: bool = True
    reroute_from_current: bool = False
    current_planet_id: Optional[str] = None
    current_tower: Optional[int] = None


@dataclass(frozen=True)
class TowerPosition:
    planet_id: str
    tower_index: int
    x_km: float
    y_km: float
    theta_degrees: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InternalLatencyBreakdown:
    planet_id: str
    entry_tower: int
    exit_tower: int
    segments_travelled: int
    distinct_towers_hit: int
    arc_length_km: float
    fiber_ms: float
    tower_processing_ms: float
    total_internal_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VoidLatencyBreakdown:
    origin_atmosphere_ms: float
    destination_atmosphere_ms: float
    void_space_ms: float
    total_void_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LinkInfo:
    from_id: str
    to_id: str
    void_distance_km: float
    send_tower: int
    receive_tower: int
    tower_distance_km: float
    void_latency: VoidLatencyBreakdown

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["void_latency"] = self.void_latency.to_dict()
        return data
