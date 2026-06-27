from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.models import UniverseConfig


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "universe-config.json"


def load_universe_config(path: str | Path | None = None) -> UniverseConfig:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"universe config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        raw = json.load(file)

    try:
        return UniverseConfig.model_validate(raw)
    except ValidationError:
        raise
    except Exception as exc:
        raise ValueError(f"invalid universe config: {exc}") from exc
