from __future__ import annotations

import math

from app.models import PlanetNode, TowerPosition, UniverseMetadata


def scaled_center(planet: PlanetNode, metadata: UniverseMetadata) -> tuple[float, float]:
    return (
        planet.x * metadata.coordinate_scale_unit_km,
        planet.y * metadata.coordinate_scale_unit_km,
    )


def tower_position(
    planet: PlanetNode,
    metadata: UniverseMetadata,
    tower_index: int,
) -> TowerPosition:
    if tower_index < 0 or tower_index >= planet.active_towers:
        raise ValueError(f"invalid tower {tower_index} for {planet.id}")

    center_x, center_y = scaled_center(planet, metadata)
    theta_degrees = 90.0 - tower_index * (360.0 / planet.active_towers)
    theta = math.radians(theta_degrees)
    return TowerPosition(
        planet_id=planet.id,
        tower_index=tower_index,
        x_km=center_x + planet.radius_km * math.cos(theta),
        y_km=center_y + planet.radius_km * math.sin(theta),
        theta_degrees=theta_degrees,
    )


def build_tower_positions(
    planets: dict[str, PlanetNode],
    metadata: UniverseMetadata,
) -> dict[str, list[TowerPosition]]:
    return {
        planet_id: [
            tower_position(planet, metadata, tower_index)
            for tower_index in range(planet.active_towers)
        ]
        for planet_id, planet in planets.items()
    }


def void_distance_km(
    origin: PlanetNode,
    destination: PlanetNode,
    metadata: UniverseMetadata,
) -> float:
    center_distance = euclidean_distance(
        scaled_center(origin, metadata),
        scaled_center(destination, metadata),
    )
    distance = (
        center_distance
        - (origin.radius_km + origin.atmosphere_thickness_km)
        - (destination.radius_km + destination.atmosphere_thickness_km)
    )
    return max(0.0, distance)

