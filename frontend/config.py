"""
Frontend configuration — reads from the shared config.json via backend.config.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import CONFIG  # noqa: E402

BACKEND_URL: str = CONFIG.get("BACKEND_URL", "http://localhost:8000")
BACKEND_PORT: int = int(CONFIG.get("BACKEND_PORT", 8000))

__all__ = ["CONFIG", "BACKEND_URL", "BACKEND_PORT"]
