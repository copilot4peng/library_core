"""
MyBagHub — FastAPI application entry point.

Startup:
    python -m backend.main

Or via uvicorn directly:
    uvicorn backend.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import CONFIG
from backend.routers import auth, projects

# ── Logging setup (must happen before any logger.xxx call) ────────────────────
logging.basicConfig(
    level=getattr(logging, CONFIG["LOG_LEVEL"], logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("mybagHub")


# ── Application lifecycle ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Ensure required storage directories exist before accepting requests."""
    storage_root = CONFIG["STORAGE_ROOT"]
    for subdir in ("user", "project"):
        path = os.path.join(storage_root, subdir)
        os.makedirs(path, exist_ok=True)
        logger.info("Storage directory ready: %s", path)

    logger.info(
        "MyBagHub backend starting on %s:%s",
        CONFIG["BACKEND_HOST"],
        CONFIG["BACKEND_PORT"],
    )
    yield
    logger.info("MyBagHub backend stopped")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="MyBagHub",
    description="Lightweight file-system-based package distribution API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten to the frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": "MyBagHub"}


# ── Dev runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=CONFIG["BACKEND_HOST"],
        port=int(CONFIG["BACKEND_PORT"]),
        reload=False,
        log_level=CONFIG["LOG_LEVEL"].lower(),
    )
