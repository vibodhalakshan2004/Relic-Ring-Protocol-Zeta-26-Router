from __future__ import annotations

from app.geometry import build_tower_positions, closest_tower_pair, scaled_center, void_distance_km
from app.latency import void_latency
from app.models import LinkInfo, PlanetNode, UniverseConfig


class UniverseGraph:
    def __init__(self, config: UniverseConfig) -> None:
        self.config = config
        self.metadata = config.universe_metadata
        self.nodes: dict[str, PlanetNode] = {node.id: node for node in config.nodes}
        self.tower_positions = build_tower_positions(self.nodes, self.metadata)
        self.links: dict[tuple[str, str], LinkInfo] = {}
        self.invalid_links: list[dict[str, object]] = []
        self._build_links()

    def _build_links(self) -> None:
        planets = list(self.nodes.values())
        for index, origin in enumerate(planets):
            for destination in planets[index + 1 :]:
                distance = void_distance_km(origin, destination, self.metadata)
                valid = distance <= self.metadata.max_void_hop_distance_km
                if valid:
                    self._add_directed_link(origin, destination, distance)
                    self._add_directed_link(destination, origin, distance)
                else:
                    self.invalid_links.append(
                        {
                            "from_id": origin.id,
                            "to_id": destination.id,
                            "void_distance_km": distance,
                            "reason": "exceeds max_void_hop_distance_km",
                        }
                    )
                    self.invalid_links.append(
                        {
                            "from_id": destination.id,
                            "to_id": origin.id,
                            "void_distance_km": distance,
                            "reason": "exceeds max_void_hop_distance_km",
                        }
                    )

    def _add_directed_link(
        self,
        origin: PlanetNode,
        destination: PlanetNode,
        distance: float,
    ) -> None:
        send_tower, receive_tower, tower_distance = closest_tower_pair(
            self.tower_positions[origin.id],
            self.tower_positions[destination.id],
        )
        self.links[(origin.id, destination.id)] = LinkInfo(
            from_id=origin.id,
            to_id=destination.id,
            void_distance_km=distance,
            send_tower=send_tower,
            receive_tower=receive_tower,
            tower_distance_km=tower_distance,
            void_latency=void_latency(origin, destination, distance, self.metadata),
        )

    def require_planet(self, planet_id: str) -> PlanetNode:
        try:
            return self.nodes[planet_id]
        except KeyError as exc:
            raise ValueError(f"unknown planet: {planet_id}") from exc

    def validate_tower(self, planet_id: str, tower_index: int) -> None:
        planet = self.require_planet(planet_id)
        if tower_index < 0 or tower_index >= planet.active_towers:
            raise ValueError(
                f"invalid tower {tower_index} for {planet_id}; "
                f"expected 0..{planet.active_towers - 1}"
            )

    def neighbors(self, planet_id: str) -> list[str]:
        return sorted(to_id for from_id, to_id in self.links if from_id == planet_id)

    def to_dict(
        self,
        failed_nodes: set[str] | None = None,
        failed_links: set[tuple[str, str]] | None = None,
    ) -> dict[str, object]:
        failed_nodes = failed_nodes or set()
        failed_links = failed_links or set()
        planets: list[dict[str, object]] = []
        for planet in self.nodes.values():
            center_x, center_y = scaled_center(planet, self.metadata)
            planets.append(
                {
                    "id": planet.id,
                    "codex": planet.codex,
                    "x": planet.x,
                    "y": planet.y,
                    "center_x_km": center_x,
                    "center_y_km": center_y,
                    "radius_km": planet.radius_km,
                    "active_towers": planet.active_towers,
                    "atmosphere_thickness_km": planet.atmosphere_thickness_km,
                    "refraction_index": planet.refraction_index,
                    "failed": planet.id in failed_nodes,
                    "towers": [
                        tower.to_dict() for tower in self.tower_positions[planet.id]
                    ],
                }
            )

        links: list[dict[str, object]] = []
        for key, link in sorted(self.links.items()):
            link_data = link.to_dict()
            link_data["failed"] = key in failed_links
            link_data["active"] = (
                link.from_id not in failed_nodes
                and link.to_id not in failed_nodes
                and key not in failed_links
            )
            links.append(link_data)

        return {
            "metadata": self.metadata.model_dump(),
            "planets": planets,
            "valid_links": links,
            "invalid_links": self.invalid_links,
            "failed_nodes": sorted(failed_nodes),
            "failed_links": [
                {"from_id": from_id, "to_id": to_id}
                for from_id, to_id in sorted(failed_links)
            ],
        }
