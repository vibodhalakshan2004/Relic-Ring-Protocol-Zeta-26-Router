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

