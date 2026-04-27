"""
Server selection page — the first step before login or registration.

The user enters the backend host and port. The frontend sends a GET /health
request to verify the service is reachable and running before proceeding.
"""
from __future__ import annotations

import httpx
from nicegui import app, ui

from frontend.auth import has_server, is_authenticated

# ── Design tokens ──────────────────────────────────────────────────────────────
_CARD = "w-96 shadow-xl rounded-2xl p-8 bg-white ring-1 ring-gray-100"
_INPUT = "w-full"
_BTN_PRIMARY = "w-full mt-4 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-xl py-2 transition-colors"
_ERR = "text-red-500 text-sm min-h-4"
_OK = "text-green-500 text-sm min-h-4"


@ui.page("/server")
async def server_select_page() -> None:
    """Server-selection page: verify backend connectivity before login."""
    # Already connected and authenticated — go straight to projects
    if has_server() and is_authenticated():
        ui.navigate.to("/projects")
        return

    ui.query("body").style("background:#f5f5f7")

    with ui.card().classes(_CARD).style(
        "position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)"
    ):
        # ── Header ────────────────────────────────────────────────────────────
        with ui.column().classes("items-center gap-1 mb-6"):
            ui.label("📦").classes("text-4xl")
            ui.label("MyBagHub").classes(
                "text-2xl font-bold text-gray-900 tracking-tight"
            )
            ui.label("Connect to a server node").classes("text-sm text-gray-400 mt-1")

        # ── Inputs ────────────────────────────────────────────────────────────
        host_in = (
            ui.input("Server IP / Hostname", placeholder="192.168.1.100")
            .classes(_INPUT)
            .props("outlined dense")
        )
        port_in = (
            ui.input("Port", placeholder="8000", value="8000")
            .classes(_INPUT)
            .props("outlined dense")
        )

        error_lbl = ui.label("").classes(_ERR)
        status_lbl = ui.label("").classes(_OK)

        # ── Connect handler ───────────────────────────────────────────────────
        async def do_connect() -> None:
            error_lbl.set_text("")
            status_lbl.set_text("")

            host = host_in.value.strip()
            port_str = port_in.value.strip()

            if not host or not port_str:
                error_lbl.set_text("Please enter both host and port")
                return

            try:
                port = int(port_str)
                if not (1 <= port <= 65535):
                    raise ValueError
            except ValueError:
                error_lbl.set_text("Port must be a number between 1 and 65535")
                return

            server_url = f"http://{host}:{port}"
            status_lbl.set_text("Connecting…")

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{server_url}/health")

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "ok":
                        app.storage.user["server_url"] = server_url
                        status_lbl.set_text(
                            f"Connected to {data.get('service', 'server')} ✓"
                        )
                        ui.navigate.to("/login")
                        return

                error_lbl.set_text("Service is not available on this server")
                status_lbl.set_text("")

            except httpx.TimeoutException:
                error_lbl.set_text("Connection timed out — check host and port")
                status_lbl.set_text("")
            except httpx.RequestError:
                error_lbl.set_text("Cannot reach the server — check host and port")
                status_lbl.set_text("")

        connect_btn = ui.button("Connect", on_click=do_connect).classes(_BTN_PRIMARY)

        # Allow pressing Enter in the port field to trigger connect
        port_in.on("keydown.enter", lambda: connect_btn.run_method("click"))
        host_in.on("keydown.enter", lambda: port_in.run_method("focus"))
