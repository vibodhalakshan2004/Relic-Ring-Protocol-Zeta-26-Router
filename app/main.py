from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config_loader import DEFAULT_CONFIG_PATH, load_universe_config
from app.failures import FailureState
from app.graph import UniverseGraph
from app.models import (
    ChaosDemoRequest,
    LinkFailureRequest,
    LoadUniverseRequest,
    NodeFailureRequest,
    PacketSendRequest,
    RouteRequest,
)
from app.packets import send_packet
from app.router import Router


class UniverseService:
    def __init__(self) -> None:
        self.config_path = DEFAULT_CONFIG_PATH
        self.graph = UniverseGraph(load_universe_config(self.config_path))
        self.failures = FailureState()

    def load(self, path: str | None = None) -> dict[str, Any]:
        self.config_path = Path(path) if path else DEFAULT_CONFIG_PATH
        self.graph = UniverseGraph(load_universe_config(self.config_path))
        self.failures.reset()
        return {
            "status": "loaded",
            "path": str(self.config_path),
            "system_name": self.graph.metadata.system_name,
            "planet_count": len(self.graph.nodes),
            "directed_link_count": len(self.graph.links),
        }


service = UniverseService()
app = FastAPI(
    title="Relic Ring Protocol - Zeta-26 Router",
    description="Tower-state routing simulator for the Launch26 Relic Ring Protocol challenge.",
    version="1.0.0",
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def api_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "system_name": service.graph.metadata.system_name}


@app.post("/universe/load")
def load_universe(request: LoadUniverseRequest) -> dict[str, Any]:
    try:
        return service.load(request.path)
    except Exception as exc:
        raise api_error(exc) from exc


@app.get("/universe")
def universe() -> dict[str, Any]:
    return {
        "metadata": service.graph.metadata.model_dump(),
        "nodes": [node.model_dump() for node in service.graph.nodes.values()],
    }


@app.get("/universe/graph")
def universe_graph() -> dict[str, Any]:
    return service.graph.to_dict(
        failed_nodes=service.failures.failed_nodes,
        failed_links=service.failures.failed_links,
    )


@app.post("/route")
def route_packet(request: RouteRequest) -> dict[str, Any]:
    try:
        router = Router(service.graph, service.failures)
        result = router.route(
            request.origin_id,
            request.destination_id,
            origin_tower=request.origin_tower,
            destination_tower=request.destination_tower,
        )
        return result
    except Exception as exc:
        raise api_error(exc) from exc


@app.post("/packet/send")
def packet_send(request: PacketSendRequest) -> dict[str, Any]:
    try:
        return send_packet(
            service.graph,
            service.failures,
            request.origin_id,
            request.destination_id,
            request.payload,
            origin_tower=request.origin_tower,
            destination_tower=request.destination_tower,
        )
    except Exception as exc:
        raise api_error(exc) from exc


@app.post("/failures/node")
def kill_node(request: NodeFailureRequest) -> dict[str, Any]:
    try:
        service.graph.require_planet(request.node_id)
        service.failures.kill_node(request.node_id)
        return service.failures.to_dict()
    except Exception as exc:
        raise api_error(exc) from exc


@app.delete("/failures/node/{node_id}")
def recover_node(node_id: str) -> dict[str, Any]:
    try:
        service.graph.require_planet(node_id)
        service.failures.recover_node(node_id)
        return service.failures.to_dict()
    except Exception as exc:
        raise api_error(exc) from exc


@app.post("/failures/link")
def kill_link(request: LinkFailureRequest) -> dict[str, Any]:
    try:
        if (request.from_id, request.to_id) not in service.graph.links:
            raise ValueError(f"unknown or invalid link: {request.from_id}->{request.to_id}")
        service.failures.kill_link(request.from_id, request.to_id, request.bidirectional)
        return service.failures.to_dict()
    except Exception as exc:
        raise api_error(exc) from exc


@app.delete("/failures/link")
def recover_link(request: LinkFailureRequest) -> dict[str, Any]:
    try:
        service.failures.recover_link(request.from_id, request.to_id, request.bidirectional)
        return service.failures.to_dict()
    except Exception as exc:
        raise api_error(exc) from exc


@app.get("/failures")
def list_failures() -> dict[str, object]:
    return service.failures.to_dict()


@app.post("/failures/reset")
def reset_failures() -> dict[str, object]:
    service.failures.reset()
    return service.failures.to_dict()


@app.post("/demo/chaos")
def demo_chaos(request: ChaosDemoRequest) -> dict[str, Any]:
    try:
        before = send_packet(
            service.graph,
            service.failures,
            request.origin_id,
            request.destination_id,
            request.payload,
            origin_tower=request.origin_tower,
            destination_tower=request.destination_tower,
        )

        applied_failure: dict[str, Any] = {"type": "none"}
        if request.fail_node_id:
            service.graph.require_planet(request.fail_node_id)
            service.failures.kill_node(request.fail_node_id)
            applied_failure = {"type": "node", "node_id": request.fail_node_id}
        elif request.fail_from_id and request.fail_to_id:
            service.failures.kill_link(
                request.fail_from_id,
                request.fail_to_id,
                request.bidirectional,
            )
            applied_failure = {
                "type": "link",
                "from_id": request.fail_from_id,
                "to_id": request.fail_to_id,
                "bidirectional": request.bidirectional,
            }

        start_state = None
        if request.reroute_from_current:
            if request.current_planet_id is None or request.current_tower is None:
                raise ValueError("current_planet_id and current_tower are required for current-state reroute")
            start_state = (request.current_planet_id, request.current_tower)

        after = send_packet(
            service.graph,
            service.failures,
            request.origin_id,
            request.destination_id,
            request.payload,
            origin_tower=request.origin_tower,
            destination_tower=request.destination_tower,
            start_state=start_state,
        )
        return {
            "before": before,
            "applied_failure": applied_failure,
            "after": after,
            "failures": service.failures.to_dict(),
        }
    except Exception as exc:
        raise api_error(exc) from exc
