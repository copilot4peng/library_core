"""
Navigation header component — Apple-style top bar.
"""
from __future__ import annotations

from nicegui import ui

from frontend.auth import get_username, logout


def nav_header(subtitle: str = "") -> None:
    """Render the top navigation bar with an optional page subtitle."""
    with ui.header().classes(
        "bg-white/80 backdrop-blur-md border-b border-gray-200 "
        "items-center px-8 py-0 gap-4 shadow-none"
    ).style("height:52px"):
        ui.label("📦 MyBagHub").classes(
            "text-base font-semibold text-gray-900 cursor-pointer tracking-tight"
        ).on("click", lambda: ui.navigate.to("/projects"))

        if subtitle:
            ui.label("/").classes("text-gray-300 text-sm")
            ui.label(subtitle).classes("text-sm text-gray-500 font-medium")

        ui.space()

        user = get_username()
        if user:
            ui.label(user).classes(
                "text-sm text-gray-500 font-medium mr-1"
            )

        ui.button(
            "Sign out",
            on_click=logout,
        ).props("flat dense").classes(
            "text-sm text-blue-500 font-medium px-3 py-1 rounded-xl "
            "hover:bg-blue-50 transition-colors"
        )


__all__ = ["nav_header"]
