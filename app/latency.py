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


def internal_latency(
    planet: PlanetNode,
    entry_tower: int,
    exit_tower: int,
    metadata: UniverseMetadata,
) -> InternalLatencyBreakdown:
    if entry_tower < 0 or entry_tower >= planet.active_towers:
        raise ValueError(f"invalid entry tower {entry_tower} for {planet.id}")
    if exit_tower < 0 or exit_tower >= planet.active_towers:
        raise ValueError(f"invalid exit tower {exit_tower} for {planet.id}")

    diff = abs(exit_tower - entry_tower)
    segments = min(diff, planet.active_towers - diff)
    distinct_towers_hit = 1 if segments == 0 else segments + 1
    arc_length_km = (2.0 * math.pi * planet.radius_km * segments) / planet.active_towers
    fiber_ms = (
        arc_length_km
        / (metadata.fiber_speed_fraction * metadata.speed_of_light_kms)
    ) * 1000.0
    tower_processing_ms = distinct_towers_hit * metadata.tower_processing_delay_ms
    return InternalLatencyBreakdown(
        planet_id=planet.id,
        entry_tower=entry_tower,
        exit_tower=exit_tower,
        segments_travelled=segments,
        distinct_towers_hit=distinct_towers_hit,
        arc_length_km=arc_length_km,
        fiber_ms=fiber_ms,
        tower_processing_ms=tower_processing_ms,
        total_internal_ms=fiber_ms + tower_processing_ms,
    )
