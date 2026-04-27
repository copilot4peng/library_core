"""
Projects list page — Apple-style layout.
"""
from __future__ import annotations

from nicegui import ui

from frontend.api import api
from frontend.auth import is_authenticated
from frontend.components.header import nav_header

# ── Design tokens ──────────────────────────────────────────────────────────────
_CARD = "w-full bg-white rounded-2xl shadow-sm ring-1 ring-gray-100 p-6"
_BTN_PRIMARY = "bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-xl px-4 py-2 transition-colors"
_BTN_OUTLINE = "bg-blue-500 text-white font-medium rounded-xl px-4 py-1.5 text-sm transition-colors"
_ERR = "text-red-500 text-sm min-h-4"


@ui.page("/projects")
async def projects_page() -> None:
    if not is_authenticated():
        ui.navigate.to("/login")
        return

    ui.query("body").style("background:#f5f5f7")
    nav_header()

    with ui.column().classes("w-full max-w-4xl mx-auto px-6 py-8 gap-6"):
        ui.label("My Projects").classes("text-2xl font-bold text-gray-900 tracking-tight")

        # ── Create project card ───────────────────────────────────────────────
        with ui.card().classes(_CARD):
            ui.label("New Project").classes("text-base font-semibold text-gray-700 mb-3")
            with ui.row().classes("w-full gap-3 items-end"):
                name_in = (
                    ui.input("Project name (letters, digits, _ -)")
                    .classes("flex-1")
                    .props("outlined dense")
                )
                create_btn = ui.button("Create", on_click=lambda: None).classes(_BTN_PRIMARY)
            create_err = ui.label("").classes(_ERR)

            async def do_create() -> None:
                create_err.set_text("")
                name = name_in.value.strip()
                if not name:
                    create_err.set_text("Name cannot be empty")
                    return
                resp = await api("POST", "/projects", json={"name": name})
                if resp.status_code == 201:
                    ui.notify(f"Project '{name}' created", type="positive")
                    name_in.set_value("")
                    await refresh()
                else:
                    try:
                        detail = resp.json().get("detail", "Failed to create project")
                    except Exception:
                        detail = f"Failed to create project (HTTP {resp.status_code})"
                    create_err.set_text(detail)

            create_btn.on("click", do_create)

        # ── Projects list ─────────────────────────────────────────────────────
        list_area = ui.column().classes("w-full gap-3")

        async def refresh() -> None:
            list_area.clear()
            resp = await api("GET", "/projects")
            if resp.status_code != 200:
                with list_area:
                    ui.label("Failed to load projects").classes("text-red-500 text-sm")
                return

            items: list[dict] = resp.json().get("data", [])
            with list_area:
                if not items:
                    with ui.card().classes(_CARD):
                        ui.label("No projects yet — create one above.").classes(
                            "text-gray-400 text-sm italic"
                        )
                    return

                for proj in items:
                    pname = proj["name"]
                    with ui.card().classes(
                        "w-full bg-white rounded-2xl shadow-sm ring-1 ring-gray-100 "
                        "px-6 py-4 flex flex-row items-center justify-between "
                        "hover:shadow-md transition-shadow cursor-default"
                    ):
                        with ui.column().classes("gap-0.5"):
                            ui.label(pname).classes("text-base font-semibold text-gray-900")
                            ui.label(f"Owner: {proj['owner']}").classes(
                                "text-xs text-gray-400"
                            )
                            members = proj.get("users", [])
                            if len(members) > 1:
                                ui.label(f"Members: {', '.join(members)}").classes(
                                    "text-xs text-gray-400"
                                )
                        ui.button(
                            "Open →",
                            on_click=lambda p=pname: ui.navigate.to(f"/projects/{p}"),
                        ).classes(_BTN_OUTLINE)

        await refresh()
