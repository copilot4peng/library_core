"""
Members tab — list current members and (for owners) add new members.
"""
from __future__ import annotations

from nicegui import ui

from frontend.api import api
from frontend.auth import get_username

# ── Design tokens ──────────────────────────────────────────────────────────────
_CARD = "w-full bg-white rounded-2xl shadow-sm ring-1 ring-gray-100 p-6"
_BTN_PRIMARY = "bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-xl px-4 py-2 transition-colors"
_ERR = "text-red-500 text-sm min-h-4"


async def render_members_tab(project_name: str) -> None:
    """Render the Members tab content inside the caller's tab panel."""
    members_area = ui.column().classes("w-full gap-4")

    async def load_members() -> None:
        members_area.clear()
        resp = await api("GET", "/projects")
        if resp.status_code != 200:
            with members_area:
                ui.label("Failed to load project info").classes("text-red-500 text-sm")
            return

        all_projects: list[dict] = resp.json().get("data", [])
        proj_info = next(
            (p for p in all_projects if p["name"] == project_name), None
        )
        if proj_info is None:
            with members_area:
                ui.label("Project not found").classes("text-red-500 text-sm")
            return

        with members_area:
            # ── Current members list ──────────────────────────────────────
            with ui.card().classes(_CARD):
                ui.label("Current Members").classes(
                    "text-base font-semibold text-gray-700 mb-3"
                )
                for member in proj_info["users"]:
                    with ui.row().classes("items-center gap-2 py-1"):
                        ui.icon("person_outline").classes("text-gray-400 text-lg")
                        ui.label(member).classes("text-sm text-gray-700 font-medium")
                        if member == proj_info["owner"]:
                            ui.badge("Owner").classes(
                                "bg-blue-50 text-blue-500 text-xs font-medium px-2 py-0.5 rounded-full"
                            )

            # ── Add member (owner only) ───────────────────────────────────
            if proj_info["owner"] == get_username():
                with ui.card().classes(_CARD):
                    ui.label("Add Member").classes(
                        "text-base font-semibold text-gray-700 mb-3"
                    )
                    with ui.row().classes("w-full gap-3 items-end"):
                        new_user_in = (
                            ui.input("Username to add")
                            .classes("flex-1")
                            .props("outlined dense")
                        )
                        add_btn = ui.button("Add", on_click=lambda: None).classes(
                            _BTN_PRIMARY
                        )
                    add_err = ui.label("").classes(_ERR)

                    async def do_add_member() -> None:
                        add_err.set_text("")
                        nu = new_user_in.value.strip()
                        if not nu:
                            add_err.set_text("Enter a username")
                            return
                        resp2 = await api(
                            "POST",
                            f"/projects/{project_name}/users",
                            params={"username": nu},
                        )
                        if resp2.status_code == 200:
                            ui.notify(f"'{nu}' added to project", type="positive")
                            new_user_in.set_value("")
                            await load_members()
                        else:
                            add_err.set_text(
                                resp2.json().get("detail", "Failed to add member")
                            )

                    add_btn.on("click", do_add_member)

    await load_members()


__all__ = ["render_members_tab"]
