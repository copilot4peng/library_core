"""Authentication endpoints: register and login."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from jose import jwt

from backend.config import CONFIG
from backend.schemas import LoginRequest, RegisterRequest, TokenResponse
from backend.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(hours=CONFIG["JWT_EXPIRE_HOURS"]),
    }
    return jwt.encode(payload, CONFIG["JWT_SECRET"], algorithm=CONFIG["JWT_ALGORITHM"])


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", status_code=201, summary="Register a new user")
async def register(req: RegisterRequest):
    try:
        auth_service.register_user(req.username, req.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "success", "message": "User registered successfully"}


@router.post("/login", response_model=TokenResponse, summary="Login and obtain a JWT")
async def login(req: LoginRequest):
    if not auth_service.verify_password(req.username, req.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    auth_service.set_user_status(req.username, "online")
    token = create_access_token(req.username)
    logger.info("User '%s' logged in", req.username)
    return TokenResponse(access_token=token)


@router.post("/logout", summary="Mark user as offline (soft logout)")
async def logout(req: LoginRequest):
    if auth_service.user_exists(req.username):
        auth_service.set_user_status(req.username, "offline")
    return {"status": "success", "message": "Logged out"}
