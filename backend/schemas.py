"""Pydantic request / response schemas for MyBagHub."""
from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9_-]{3,50}", v):
            raise ValueError(
                "Username must be 3-50 characters: letters, digits, underscores or hyphens"
            )
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Projects ──────────────────────────────────────────────────────────────────

class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", v):
            raise ValueError(
                "Project name must be 1-100 characters: letters, digits, underscores or hyphens"
            )
        return v


class ProjectResponse(BaseModel):
    name: str
    owner: str
    users: list[str]


class VersionInfo(BaseModel):
    version: str
    file_name: str
    upload_at: str
    size: int


class UploadResponse(BaseModel):
    project: str
    version: str
    path: str
    size: int
