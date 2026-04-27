"""Configuration loader for MyBagHub."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_CONFIG: dict = {
    "STORAGE_ROOT": "/data",
    "MAX_FILE_SIZE": 524288000,   # 500 MB in bytes
    "JWT_SECRET": "insecure-default-secret-please-change",
    "JWT_ALGORITHM": "HS256",
    "JWT_EXPIRE_HOURS": 24,
    "BACKEND_HOST": "0.0.0.0",
    "BACKEND_PORT": 8000,
    "LOG_LEVEL": "INFO",
}


def _resolve_candidates(config_path: str | None) -> list[Path]:
    project_root = Path(__file__).parent.parent
    backend_dir = Path(__file__).parent
    candidates: list[Path] = []

    env_path = os.getenv("MY_LIBRARY_CONFIG_PATH")
    if env_path:
        candidates.append(Path(env_path))

    if config_path:
        requested = Path(config_path)
        if not requested.is_absolute():
            requested = project_root / requested
        candidates.append(requested)
    else:
        candidates.append(Path("/config/config.json"))
        candidates.append(backend_dir / "config.json")  # backend-local config for dev
        candidates.append(project_root / "config.json")  # legacy root config

    unique_candidates: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved_candidate = candidate.resolve(strict=False)
        if resolved_candidate not in seen:
            unique_candidates.append(resolved_candidate)
            seen.add(resolved_candidate)
    return unique_candidates


def load_config(config_path: str | None = None) -> dict:
    """Load configuration from mounted or local config files over defaults."""
    config = DEFAULT_CONFIG.copy()

    candidates = _resolve_candidates(config_path)
    for resolved in candidates:
        if not resolved.exists():
            continue
        try:
            with open(resolved, encoding="utf-8") as fh:
                file_config: dict = json.load(fh)
            config.update(file_config)
            logger.info("Loaded config from %s", resolved)
            return config
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(
                "Failed to load config from %s (%s). Using defaults.", resolved, exc
            )

    logger.info("No config file found in %s — using built-in defaults.", candidates)

    return config


# Module-level singleton used by all other modules
CONFIG: dict = load_config()
