"""
Root page — redirects to /projects when authenticated, otherwise to /login.
"""
from __future__ import annotations

from nicegui import ui

from frontend.auth import is_authenticated


@ui.page("/")
async def root_page() -> None:
    if is_authenticated():
        ui.navigate.to("/projects")
    else:
        ui.navigate.to("/login")
