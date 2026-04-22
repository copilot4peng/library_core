"""FastAPI dependency: JWT bearer authentication."""
from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException, Query
from jose import JWTError, jwt

from backend.config import CONFIG


async def get_current_user(authorization: str = Header(None)) -> str:
    """
    Extract the username from the *Authorization: Bearer <token>* header.
    Raises HTTP 401 on missing or invalid tokens.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ", 1)[1]
    return _decode_token(token)


async def get_current_user_query_token(
    authorization: str = Header(None),
    token: Optional[str] = Query(None),
) -> str:
    """
    Like *get_current_user* but also accepts a *token* query parameter.
    Used exclusively by the download endpoint so that browsers can fetch files
    directly without custom headers.
    """
    bearer_token: Optional[str] = None
    if authorization and authorization.startswith("Bearer "):
        bearer_token = authorization.split(" ", 1)[1]
    elif token:
        bearer_token = token

    if not bearer_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return _decode_token(bearer_token)


def _decode_token(token: str) -> str:
    try:
        payload: dict = jwt.decode(
            token,
            CONFIG["JWT_SECRET"],
            algorithms=[CONFIG["JWT_ALGORITHM"]],
        )
        username: Optional[str] = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
