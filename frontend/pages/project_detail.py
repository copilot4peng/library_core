"""
Project detail page — assembles Versions, Audit Log and Members tabs.
"""
from __future__ import annotations

from nicegui import ui

from frontend.auth import is_authenticated
from frontend.components.header import nav_header
from frontend.pages.project_detail.audit_log_tab import render_audit_log_tab
from frontend.pages.project_detail.members_tab import render_members_tab
from frontend.pages.project_detail.versions_tab import render_versions_tab


@ui.page("/projects/{name}")
async def project_detail_page(name: str) -> None:
    if not is_authenticated():
        ui.navigate.to("/login")
        return

    ui.query("body").style("background:#f5f5f7")
    nav_header(subtitle=name)

    with ui.column().classes("w-full max-w-5xl mx-auto px-6 py-8 gap-6"):
        ui.label(name).classes("text-2xl font-bold text-gray-900 tracking-tight")

        # ── Tab bar ───────────────────────────────────────────────────────────
        with ui.tabs().classes(
            "w-full border-b border-gray-200 bg-transparent"
        ).props("indicator-color=blue-500 active-color=blue-500") as tabs:
            tab_versions = ui.tab("Versions").classes(
                "text-sm font-medium text-gray-500"
            )
            tab_logs = ui.tab("Audit Log").classes(
                "text-sm font-medium text-gray-500"
            )
            tab_members = ui.tab("Members").classes(
                "text-sm font-medium text-gray-500"
            )

        with ui.tab_panels(tabs, value=tab_versions).classes(
            "w-full bg-transparent pt-4"
        ):
            with ui.tab_panel(tab_versions):
                await render_versions_tab(project_name=name)

            with ui.tab_panel(tab_logs):
                await render_audit_log_tab(project_name=name)

            with ui.tab_panel(tab_members):
                await render_members_tab(project_name=name)
