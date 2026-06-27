from __future__ import annotations

import math

from app.models import (
    InternalLatencyBreakdown,
    PlanetNode,
    UniverseMetadata,
    VoidLatencyBreakdown,
)


def void_latency(
    origin: PlanetNode,
    destination: PlanetNode,
    void_distance_km: float,
    metadata: UniverseMetadata,
) -> VoidLatencyBreakdown:
    origin_atmosphere_ms = (
        (origin.atmosphere_thickness_km * origin.refraction_index)
        / metadata.speed_of_light_kms
    ) * 1000.0
    destination_atmosphere_ms = (
        (destination.atmosphere_thickness_km * destination.refraction_index)
        / metadata.speed_of_light_kms
    ) * 1000.0
    void_space_ms = (void_distance_km / metadata.speed_of_light_kms) * 1000.0
    return VoidLatencyBreakdown(
        origin_atmosphere_ms=origin_atmosphere_ms,
        destination_atmosphere_ms=destination_atmosphere_ms,
        void_space_ms=void_space_ms,
        total_void_ms=origin_atmosphere_ms + destination_atmosphere_ms + void_space_ms,
    )

