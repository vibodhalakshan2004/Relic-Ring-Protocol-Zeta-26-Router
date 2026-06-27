from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from app.codex import (
    bytes_to_text,
    decode_payload_from_codex,
    encode_payload_for_codex,
    text_to_ascii_bytes,
)
from app.failures import FailureState
from app.graph import UniverseGraph
from app.router import Router, State


def send_packet(
    graph: UniverseGraph,
    failures: FailureState,
    origin_id: str,
    destination_id: str,
    payload: str,
    origin_tower: Optional[int] = None,
    destination_tower: Optional[int] = None,
    start_state: Optional[State] = None,
) -> dict[str, Any]:
    router = Router(graph, failures)
    route = router.route(
        origin_id,
        destination_id,
        origin_tower=origin_tower,
        destination_tower=destination_tower,
        start_state=start_state,
    )
    packet_id = str(uuid4())
    canonical_bytes = text_to_ascii_bytes(payload)

    if route["status"] != "ok":
        return {
            "packet_id": packet_id,
            "origin_id": origin_id,
            "destination_id": destination_id,
            "current_id": origin_id,
            "payload": payload,
            "canonical_payload_bytes": canonical_bytes,
            "hop_log": [],
            **route,
        }

    packet_hops: list[dict[str, Any]] = []
    for hop in route["hop_log"]:
        from_planet = graph.nodes[hop["from_planet"]]
        to_planet = graph.nodes[hop["to_planet"]]
        encoded = encode_payload_for_codex(canonical_bytes, to_planet.codex)
        decoded = decode_payload_from_codex(encoded, to_planet.codex)
        packet_hop = {
            **hop,
            "from_codex": from_planet.codex,
            "to_codex": to_planet.codex,
            "payload_encoded_in_next_codex": encoded,
            "void_stream": " ".join(encoded),
            "decoded_payload_at_receiver": bytes_to_text(decoded),
        }
        packet_hops.append(packet_hop)

    return {
        "packet_id": packet_id,
        "origin_id": origin_id,
        "destination_id": destination_id,
        "current_id": destination_id,
        "payload": payload,
        "canonical_payload_bytes": canonical_bytes,
        "current_codex": graph.nodes[destination_id].codex,
        "status": "delivered",
        "route": route["route"],
        "states": route["states"],
        "total_latency_ms": route["total_latency_ms"],
        "latency_breakdown": route["latency_breakdown"],
        "hop_log": packet_hops,
        "delivered_payload": payload,
        "failed_nodes_used_for_calculation": route["failed_nodes_used_for_calculation"],
        "failed_links_used_for_calculation": route["failed_links_used_for_calculation"],
        "final_internal": route["final_internal"],
    }
