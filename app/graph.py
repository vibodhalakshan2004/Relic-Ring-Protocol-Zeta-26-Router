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
