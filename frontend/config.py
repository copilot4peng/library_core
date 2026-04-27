"""
Frontend configuration — standalone loader, independent of the backend.

Config search order (first match wins):
  1. MY_LIBRARY_FRONTEND_CONFIG_PATH env var
  2. /config/config.json  (Docker volume mount)
  3. <this_file's_directory>/config.json  (local dev)
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: dict = {
    "FRONTEND_HOST": "0.0.0.0",
    "FRONTEND_PORT": 8080,
    "STORAGE_SECRET": "nicegui-fallback-secret",
    "MAX_FILE_SIZE": 524288000,   # 500 MB — matches backend default
    "LOG_LEVEL": "INFO",
}


def load_config() -> dict:
    """Load frontend configuration from file over built-in defaults."""
    config = DEFAULT_CONFIG.copy()

    candidates: list[Path] = []
    env_path = os.getenv("MY_LIBRARY_FRONTEND_CONFIG_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(Path("/config/config.json"))
    candidates.append(Path(__file__).parent / "config.json")

    seen: set[Path] = set()
    for p in candidates:
        resolved = p.resolve(strict=False)
        if resolved in seen:
            continue
        seen.add(resolved)
        if not resolved.exists():
            continue
        try:
            with open(resolved, encoding="utf-8") as fh:
                config.update(json.load(fh))
            logger.info("Loaded frontend config from %s", resolved)
            return config
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load frontend config from %s (%s)", resolved, exc)

    logger.info("No frontend config file found — using built-in defaults.")
    return config


CONFIG: dict = load_config()

__all__ = ["CONFIG"]
