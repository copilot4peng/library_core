"""
Login page — Apple-style card centred on the screen.
"""
from __future__ import annotations

import httpx
from nicegui import app, ui

from frontend.api import api
from frontend.auth import has_server, is_authenticated

# ── Design tokens ──────────────────────────────────────────────────────────────
_CARD = "w-96 shadow-xl rounded-2xl p-8 bg-white ring-1 ring-gray-100"
_INPUT = "w-full"
_BTN_PRIMARY = "w-full mt-4 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-xl py-2 transition-colors"
_ERR = "text-red-500 text-sm min-h-4"


@ui.page("/login")
async def login_page() -> None:
    if not has_server():
        ui.navigate.to("/server")
        return
    if is_authenticated():
        ui.navigate.to("/projects")
        return

    # Light gray page background
    ui.query("body").style("background:#f5f5f7")

    with ui.card().classes(_CARD).style("position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)"):
        # App logo / title
        with ui.column().classes("items-center gap-1 mb-6"):
            ui.label("📦").classes("text-4xl")
            ui.label("MyBagHub").classes("text-2xl font-bold text-gray-900 tracking-tight")
            ui.label("Sign in to continue").classes("text-sm text-gray-400 mt-1")

        username_in = ui.input("Username").classes(_INPUT).props("outlined dense")
        password_in = (
            ui.input("Password", password=True, password_toggle_button=True)
            .classes(_INPUT)
            .props("outlined dense")
        )
        error_lbl = ui.label("").classes(_ERR)

        async def do_login() -> None:
            error_lbl.set_text("")
            u, p = username_in.value.strip(), password_in.value
            if not u or not p:
                error_lbl.set_text("Please enter username and password")
                return
            try:
                resp = await api("POST", "/auth/login", json={"username": u, "password": p})
            except httpx.RequestError:
                error_lbl.set_text("Cannot reach the backend — try reconnecting on the server page")
                return

            if resp.status_code == 200:
                data = resp.json()
                app.storage.user["token"] = data["access_token"]
                app.storage.user["username"] = u
                ui.navigate.to("/projects")
            else:
                try:
                    detail = resp.json().get("detail", "Login failed")
                except Exception:
                    detail = f"Login failed (HTTP {resp.status_code})"
                error_lbl.set_text(detail)

        ui.button("Sign in", on_click=do_login).classes(_BTN_PRIMARY)

        ui.separator().classes("my-4 bg-gray-100")

        with ui.row().classes("w-full justify-center gap-1 text-sm"):
            ui.label("No account?").classes("text-gray-500")
            ui.link("Create one", "/register").classes("text-blue-500 font-medium")

        with ui.row().classes("w-full justify-center gap-1 text-sm mt-1"):
            ui.label("Wrong server?").classes("text-gray-500")
            ui.link("Change server", "/server").classes("text-blue-500 font-medium")
