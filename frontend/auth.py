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


def get_server_url() -> Optional[str]:
    """Return the backend URL chosen by the user on the server-selection page."""
    return app.storage.user.get("server_url")


def has_server() -> bool:
    """Return True when the user has selected and verified a backend server."""
    return bool(get_server_url())


def logout() -> None:
    app.storage.user.clear()
    ui.navigate.to("/server")


__all__ = [
    "get_token",
    "get_username",
    "is_authenticated",
    "get_server_url",
    "has_server",
    "logout",
]
