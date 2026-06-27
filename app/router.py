from __future__ import annotations

import heapq
from typing import Any, Optional

from app.failures import FailureState
from app.graph import UniverseGraph
from app.latency import internal_latency


State = tuple[str, int]


class Router:
    def __init__(self, graph: UniverseGraph, failures: FailureState) -> None:
        self.graph = graph
        self.failures = failures

    def route(
        self,
        origin_id: str,
        destination_id: str,
        origin_tower: Optional[int] = None,
        destination_tower: Optional[int] = None,
        start_state: Optional[State] = None,
    ) -> dict[str, Any]:
        self._validate_route_request(
            origin_id,
            destination_id,
            origin_tower,
            destination_tower,
            start_state,
        )

        if origin_id == destination_id:
            return self._same_planet_route(origin_id, origin_tower, destination_tower)

        start_states = self._start_states(origin_id, origin_tower, start_state)
        distances: dict[State, float] = {}
        predecessors: dict[State, dict[str, Any]] = {}
        queue: list[tuple[float, int, State]] = []
        counter = 0

        for state in start_states:
            distances[state] = 0.0
            heapq.heappush(queue, (0.0, counter, state))
            counter += 1

        best_destination_state: State | None = None
        best_total = float("inf")
        final_internal: dict[str, Any] | None = None

        while queue:
            current_cost, _, state = heapq.heappop(queue)
            if current_cost > distances.get(state, float("inf")):
                continue
            current_planet_id, entry_tower = state

            if current_planet_id == destination_id:
                candidate_total = current_cost
                candidate_final = None
                if destination_tower is not None:
                    breakdown = internal_latency(
                        self.graph.nodes[current_planet_id],
                        entry_tower,
                        destination_tower,
                        self.graph.metadata,
                    )
                    candidate_total += breakdown.total_internal_ms
                    candidate_final = breakdown.to_dict()
                if candidate_total < best_total:
                    best_total = candidate_total
                    best_destination_state = state
                    final_internal = candidate_final
                if destination_tower is None:
                    break
                continue

            if current_cost >= best_total:
                continue

            for next_planet_id in self.graph.neighbors(current_planet_id):
                if self._blocked(current_planet_id, next_planet_id):
                    continue

                link = self.graph.links[(current_planet_id, next_planet_id)]
                current_planet = self.graph.nodes[current_planet_id]
                internal = internal_latency(
                    current_planet,
                    entry_tower,
                    link.send_tower,
                    self.graph.metadata,
                )
                transition_latency = (
                    internal.total_internal_ms + link.void_latency.total_void_ms
                )
                next_state = (next_planet_id, link.receive_tower)
                new_cost = current_cost + transition_latency

                if new_cost < distances.get(next_state, float("inf")):
                    distances[next_state] = new_cost
                    predecessors[next_state] = {
                        "previous_state": state,
                        "from_planet": current_planet_id,
                        "to_planet": next_planet_id,
                        "send_tower": link.send_tower,
                        "receive_tower": link.receive_tower,
                        "internal": internal.to_dict(),
                        "void": {
                            "void_distance_km": link.void_distance_km,
                            **link.void_latency.to_dict(),
                        },
                        "tower_distance_km": link.tower_distance_km,
                        "transition_latency_ms": transition_latency,
                        "cumulative_latency_ms": new_cost,
                    }
                    heapq.heappush(queue, (new_cost, counter, next_state))
                    counter += 1

        if best_destination_state is None:
            return {
                "status": "undeliverable",
                "reason": "no active route available",
                "failed_nodes_used_for_calculation": sorted(self.failures.failed_nodes),
                "failed_links_used_for_calculation": self._serialized_failed_links(),
            }

        return self._build_route_result(
            best_destination_state,
            predecessors,
            best_total,
            final_internal,
        )

    def _validate_route_request(
        self,
        origin_id: str,
        destination_id: str,
        origin_tower: Optional[int],
        destination_tower: Optional[int],
        start_state: Optional[State],
    ) -> None:
        self.graph.require_planet(origin_id)
        self.graph.require_planet(destination_id)
        if self.failures.is_node_failed(origin_id):
            raise ValueError(f"origin planet is failed: {origin_id}")
        if self.failures.is_node_failed(destination_id):
            raise ValueError(f"destination planet is failed: {destination_id}")
        if origin_tower is not None:
            self.graph.validate_tower(origin_id, origin_tower)
        if destination_tower is not None:
            self.graph.validate_tower(destination_id, destination_tower)
        if start_state is not None:
            start_planet_id, start_tower = start_state
            self.graph.require_planet(start_planet_id)
            if self.failures.is_node_failed(start_planet_id):
                raise ValueError(f"start planet is failed: {start_planet_id}")
            self.graph.validate_tower(start_planet_id, start_tower)

    def _start_states(
        self,
        origin_id: str,
        origin_tower: Optional[int],
        start_state: Optional[State],
    ) -> list[State]:
        if start_state is not None:
            return [start_state]
        if origin_tower is not None:
            return [(origin_id, origin_tower)]
        return [
            (origin_id, tower_index)
            for tower_index in range(self.graph.nodes[origin_id].active_towers)
        ]

    def _blocked(self, from_id: str, to_id: str) -> bool:
        return (
            self.failures.is_node_failed(from_id)
            or self.failures.is_node_failed(to_id)
            or self.failures.is_link_failed(from_id, to_id)
        )

    def _same_planet_route(
        self,
        planet_id: str,
        origin_tower: Optional[int],
        destination_tower: Optional[int],
    ) -> dict[str, Any]:
        planet = self.graph.nodes[planet_id]
        start_tower = origin_tower if origin_tower is not None else 0
        final_internal = None
        total_latency = 0.0
        if destination_tower is not None:
            breakdown = internal_latency(
                planet,
                start_tower,
                destination_tower,
                self.graph.metadata,
            )
            final_internal = breakdown.to_dict()
            total_latency = breakdown.total_internal_ms
        return {
            "status": "ok",
            "route": [planet_id],
            "states": [
                {
                    "planet": planet_id,
                    "tower": destination_tower
                    if destination_tower is not None
                    else start_tower,
                }
            ],
            "total_latency_ms": total_latency,
            "hop_log": [],
            "latency_breakdown": {
                "internal_ms": total_latency,
                "void_ms": 0.0,
                "tower_processing_ms": final_internal["tower_processing_ms"]
                if final_internal
                else 0.0,
                "fiber_ms": final_internal["fiber_ms"] if final_internal else 0.0,
                "atmosphere_ms": 0.0,
            },
            "final_internal": final_internal,
            "failed_nodes_used_for_calculation": sorted(self.failures.failed_nodes),
            "failed_links_used_for_calculation": self._serialized_failed_links(),
        }

    def _build_route_result(
        self,
        destination_state: State,
        predecessors: dict[State, dict[str, Any]],
        total_latency_ms: float,
        final_internal: dict[str, Any] | None,
    ) -> dict[str, Any]:
        states: list[State] = [destination_state]
        hops: list[dict[str, Any]] = []
        current = destination_state
        while current in predecessors:
            hop = predecessors[current]
            hops.append(hop)
            current = hop["previous_state"]
            states.append(current)

        states.reverse()
        hops.reverse()

        hop_log: list[dict[str, Any]] = []
        internal_ms = 0.0
        void_ms = 0.0
        tower_ms = 0.0
        fiber_ms = 0.0
        atmosphere_ms = 0.0

        for index, hop in enumerate(hops, start=1):
            internal = hop["internal"]
            void = hop["void"]
            internal_ms += internal["total_internal_ms"]
            void_ms += void["total_void_ms"]
            tower_ms += internal["tower_processing_ms"]
            fiber_ms += internal["fiber_ms"]
            atmosphere_ms += (
                void["origin_atmosphere_ms"] + void["destination_atmosphere_ms"]
            )
            hop_log.append(
                {
                    "hop_index": index,
                    "from_planet": hop["from_planet"],
                    "to_planet": hop["to_planet"],
                    "sending_tower": hop["send_tower"],
                    "receiving_tower": hop["receive_tower"],
                    "tower_distance_km": hop["tower_distance_km"],
                    "internal_routing": internal,
                    "void_transmission": void,
                    "hop_total_latency_ms": hop["transition_latency_ms"],
                    "cumulative_latency_ms": hop["cumulative_latency_ms"],
                }
            )

        
        return {
            "status": "ok",
            "route": [planet_id for planet_id, _ in states],
            "states": [
                {"planet": planet_id, "tower": tower_index}
                for planet_id, tower_index in states
            ],
            "total_latency_ms": total_latency_ms,
            "hop_log": hop_log,
            "latency_breakdown": {
                "internal_ms": internal_ms,
                "void_ms": void_ms,
                "tower_processing_ms": tower_ms,
                "fiber_ms": fiber_ms,
                "atmosphere_ms": atmosphere_ms,
            },
            "final_internal": final_internal,
            "failed_nodes_used_for_calculation": sorted(self.failures.failed_nodes),
            "failed_links_used_for_calculation": self._serialized_failed_links(),
        }

    def _serialized_failed_links(self) -> list[dict[str, str]]:
        return [
            {"from_id": from_id, "to_id": to_id}
            for from_id, to_id in sorted(self.failures.failed_links)
        ]
