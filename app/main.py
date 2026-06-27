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


