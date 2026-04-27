"""
Registration page — Apple-style card centred on the screen.
"""
from __future__ import annotations

import httpx
from nicegui import ui

from frontend.api import api
from frontend.auth import has_server, is_authenticated

# ── Design tokens ──────────────────────────────────────────────────────────────
_CARD = "w-96 shadow-xl rounded-2xl p-8 bg-white ring-1 ring-gray-100"
_INPUT = "w-full"
_BTN_PRIMARY = "w-full mt-4 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-xl py-2 transition-colors"
_ERR = "text-red-500 text-sm min-h-4"


@ui.page("/register")
async def register_page() -> None:
    if not has_server():
        ui.navigate.to("/server")
        return
    if is_authenticated():
        ui.navigate.to("/projects")
        return

    ui.query("body").style("background:#f5f5f7")

    with ui.card().classes(_CARD).style("position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)"):
        with ui.column().classes("items-center gap-1 mb-6"):
            ui.label("📦").classes("text-4xl")
            ui.label("Create Account").classes("text-2xl font-bold text-gray-900 tracking-tight")
            ui.label("Join MyBagHub today").classes("text-sm text-gray-400 mt-1")

        username_in = ui.input("Username").classes(_INPUT).props("outlined dense")
        password_in = (
            ui.input("Password", password=True, password_toggle_button=True)
            .classes(_INPUT)
            .props("outlined dense")
        )
        confirm_in = (
            ui.input("Confirm Password", password=True, password_toggle_button=True)
            .classes(_INPUT)
            .props("outlined dense")
        )
        error_lbl = ui.label("").classes(_ERR)

        async def do_register() -> None:
            error_lbl.set_text("")
            u = username_in.value.strip()
            p, c = password_in.value, confirm_in.value
            if not u or not p:
                error_lbl.set_text("Username and password are required")
                return
            if p != c:
                error_lbl.set_text("Passwords do not match")
                return
            try:
                resp = await api("POST", "/auth/register", json={"username": u, "password": p})
            except httpx.RequestError:
                error_lbl.set_text("Cannot reach the backend")
                return

            if resp.status_code == 201:
                ui.notify("Registration successful — please sign in", type="positive")
                ui.navigate.to("/login")
            else:
                try:
                    detail = resp.json().get("detail", "Registration failed")
                except Exception:
                    detail = f"Registration failed (HTTP {resp.status_code})"
                error_lbl.set_text(detail)

        ui.button("Create Account", on_click=do_register).classes(_BTN_PRIMARY)

        ui.separator().classes("my-4 bg-gray-100")

        with ui.row().classes("w-full justify-center gap-1 text-sm"):
            ui.label("Already have an account?").classes("text-gray-500")
            ui.link("Sign in", "/login").classes("text-blue-500 font-medium")
