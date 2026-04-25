"""
Audit Log tab — shows the project's audit log entries, newest first.
"""
from __future__ import annotations

from nicegui import ui

from frontend.api import api

# ── Design tokens ──────────────────────────────────────────────────────────────
_CARD = "w-full bg-white rounded-2xl shadow-sm ring-1 ring-gray-100"


async def render_audit_log_tab(project_name: str) -> None:
    """Render the Audit Log tab content inside the caller's tab panel."""
    logs_area = ui.column().classes("w-full gap-2")

    async def load_logs() -> None:
        logs_area.clear()
        resp = await api("GET", f"/projects/{project_name}/logs")
        if resp.status_code != 200:
            with logs_area:
                ui.label("Failed to load audit log").classes("text-red-500 text-sm")
            return

        entries: list[str] = resp.json().get("data", [])
        with logs_area:
            if not entries:
                with ui.card().classes(_CARD + " p-6"):
                    ui.label("No audit entries yet.").classes(
                        "text-gray-400 text-sm italic"
                    )
                return

            # Show newest first
            for line in reversed(entries):
                parts = line.split("|", 3)
                with ui.card().classes(_CARD + " px-5 py-3"):
                    if len(parts) == 4:
                        ts, user, action, detail = parts
                        with ui.row().classes("gap-4 items-center flex-wrap"):
                            ui.label(ts.strip()).classes(
                                "text-xs text-gray-400 font-mono w-36"
                            )
                            ui.label(user.strip()).classes(
                                "text-xs font-semibold text-gray-700 w-24"
                            )
                            ui.label(action.strip()).classes(
                                "text-xs text-blue-500 font-medium w-36"
                            )
                            ui.label(detail.strip()).classes(
                                "text-xs text-gray-500"
                            )
                    else:
                        ui.label(line).classes("text-xs font-mono text-gray-400")

    await load_logs()


__all__ = ["render_audit_log_tab"]
