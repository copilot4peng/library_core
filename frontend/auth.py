"""
Session / authentication helpers.

All page modules import from here so session state is managed in one place.
"""
from __future__ import annotations

from typing import Optional

from nicegui import app, ui


def get_token() -> Optional[str]:
    return app.storage.user.get("token")


def get_username() -> Optional[str]:
    return app.storage.user.get("username")


def is_authenticated() -> bool:
    return bool(get_token())


def logout() -> None:
    app.storage.user.clear()
    ui.navigate.to("/login")


__all__ = ["get_token", "get_username", "is_authenticated", "logout"]
