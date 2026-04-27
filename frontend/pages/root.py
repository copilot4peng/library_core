"""
Root page — redirects based on session state:
  /server  if no backend server has been selected yet
  /login   if the user is not authenticated
  /projects if the user is authenticated
"""
from __future__ import annotations

from nicegui import ui

from frontend.auth import has_server, is_authenticated


@ui.page("/")
async def root_page() -> None:
    if not has_server():
        ui.navigate.to("/server")
    elif is_authenticated():
        ui.navigate.to("/projects")
    else:
        ui.navigate.to("/login")
