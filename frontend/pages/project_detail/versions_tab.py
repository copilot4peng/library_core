"""
Versions tab — upload a new version and list existing ones.
"""
from __future__ import annotations

import logging

import httpx
from nicegui import ui
from nicegui.events import UploadEventArguments

from frontend.api import api, open_download
from frontend.config import CONFIG

logger = logging.getLogger("mybagHub.frontend.versions_tab")

# ── Design tokens ──────────────────────────────────────────────────────────────
_CARD = "w-full bg-white rounded-2xl shadow-sm ring-1 ring-gray-100 p-6"
_BTN_PRIMARY = "bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-xl px-4 py-2 transition-colors"
_BTN_DOWNLOAD = "bg-green-500 hover:bg-green-600 text-white font-medium rounded-xl px-3 py-1.5 text-sm transition-colors"


async def render_versions_tab(project_name: str) -> None:
    """Render the Versions tab content inside the caller's tab panel."""

    # ── Upload section ────────────────────────────────────────────────────────
    with ui.card().classes(_CARD + " mb-4"):
        ui.label("Upload New Version").classes("text-base font-semibold text-gray-700 mb-4")

        version_in = (
            ui.input("Version tag (e.g. v1.0 or v2.3.1)")
            .classes("w-full")
            .props("outlined dense")
        )
        about_in = (
            ui.textarea("Description (optional)")
            .classes("w-full")
            .props("outlined autogrow")
        )

        pending: dict = {}
        file_status = ui.label("No file selected").classes("text-xs text-gray-400 mt-1")
        upload_msg = ui.label("").classes("text-sm min-h-4")

        async def on_file_received(e: UploadEventArguments) -> None:
            try:
                data = await e.file.read()
                fname = e.file.name
            except Exception as exc:
                logger.exception("Failed to read uploaded file content")
                pending.clear()
                file_status.set_text("No file selected")
                file_status.classes(remove="text-green-500", add="text-gray-400")
                upload_msg.set_text(f"Failed to process selected file: {exc}")
                upload_msg.classes(remove="text-green-500", add="text-red-500")
                return

            if not data:
                pending.clear()
                file_status.set_text("No file selected")
                file_status.classes(remove="text-green-500", add="text-gray-400")
                upload_msg.set_text("Selected file is empty or could not be read")
                upload_msg.classes(remove="text-green-500", add="text-red-500")
                return

            pending["data"] = data
            pending["name"] = fname
            size_kb = len(data) / 1024
            file_status.set_text(f"Selected: {fname}  ({size_kb:,.1f} KB)")
            file_status.classes(remove="text-gray-400", add="text-green-500")
            upload_msg.set_text("File ready to upload")
            upload_msg.classes(remove="text-red-500 text-blue-500", add="text-green-500")

        def on_file_rejected() -> None:
            pending.clear()
            file_status.set_text("No file selected")
            file_status.classes(remove="text-green-500", add="text-gray-400")
            max_mb = CONFIG.get("MAX_FILE_SIZE", 0) / (1024 * 1024)
            upload_msg.set_text(f"File rejected. Limit: {max_mb:.0f} MB")
            upload_msg.classes(remove="text-green-500 text-blue-500", add="text-red-500")

        ui.upload(
            label="Drop .tar.gz file here (or click to browse)",
            on_upload=on_file_received,
            on_rejected=on_file_rejected,
            auto_upload=True,
            multiple=False,
            max_file_size=int(CONFIG.get("MAX_FILE_SIZE", 524288000)),
        ).classes("w-full mt-2").props("accept='.tar.gz,application/gzip'")

        async def do_upload() -> None:
            upload_msg.set_text("")
            ver = version_in.value.strip()
            if not ver:
                upload_msg.set_text("Please enter a version tag")
                upload_msg.classes(remove="text-green-500", add="text-red-500")
                return
            if not pending.get("data"):
                upload_msg.set_text("Please select a .tar.gz file first")
                upload_msg.classes(remove="text-green-500", add="text-red-500")
                return

            upload_msg.set_text("Uploading…")
            upload_msg.classes(remove="text-red-500 text-green-500", add="text-blue-500")

            file_tuple = (pending["name"], pending["data"], "application/gzip")
            try:
                resp = await api(
                    "POST",
                    f"/projects/{project_name}/versions",
                    files={"file": file_tuple},
                    data={"version": ver, "about": about_in.value.strip()},
                )
            except httpx.RequestError:
                upload_msg.set_text("Network error — upload failed")
                upload_msg.classes(remove="text-blue-500", add="text-red-500")
                return

            if resp.status_code == 200:
                upload_msg.set_text(f"✓ Uploaded {pending['name']} as {ver}")
                upload_msg.classes(remove="text-red-500 text-blue-500", add="text-green-500")
                pending.clear()
                file_status.set_text("No file selected")
                file_status.classes(remove="text-green-500", add="text-gray-400")
                version_in.set_value("")
                about_in.set_value("")
                await refresh_versions()
            else:
                try:
                    detail = resp.json().get("detail", "Upload failed")
                except Exception:
                    detail = f"Upload failed (HTTP {resp.status_code})"
                upload_msg.set_text(detail)
                upload_msg.classes(remove="text-blue-500 text-green-500", add="text-red-500")

        ui.button("Upload Version", on_click=do_upload).classes(_BTN_PRIMARY + " mt-3")

    # ── Version list ──────────────────────────────────────────────────────────
    versions_area = ui.column().classes("w-full gap-3")

    async def refresh_versions() -> None:
        versions_area.clear()
        resp = await api("GET", f"/projects/{project_name}/versions")
        if resp.status_code != 200:
            with versions_area:
                ui.label("Failed to load versions").classes("text-red-500 text-sm")
            return

        items: list[dict] = resp.json().get("data", [])
        with versions_area:
            if not items:
                with ui.card().classes(_CARD):
                    ui.label("No versions uploaded yet.").classes(
                        "text-gray-400 text-sm italic"
                    )
                return
            for v in items:
                ver_tag = v["version"]
                fname = v["file_name"]
                size_mb = v.get("size", 0) / (1024 * 1024)
                uploaded = v["upload_at"][:19].replace("T", " ")
                about = (v.get("about") or "").strip()

                with ui.card().classes(
                    "w-full bg-white rounded-2xl shadow-sm ring-1 ring-gray-100 px-5 py-4"
                ):
                    with ui.row().classes("w-full items-center justify-between gap-4"):
                        with ui.column().classes("gap-0.5 flex-1 min-w-0"):
                            ui.label(ver_tag).classes(
                                "font-semibold text-gray-900 text-base"
                            )
                            ui.label(fname).classes("text-sm text-gray-500 truncate")
                            ui.label(
                                f"{size_mb:.2f} MB  ·  {uploaded} UTC"
                            ).classes("text-xs text-gray-400")
                            if about:
                                ui.markdown(about).classes("text-sm text-gray-600 mt-1")

                        ui.button(
                            "⬇ Download",
                            on_click=lambda pn=project_name, vt=ver_tag: open_download(pn, vt),
                        ).classes(_BTN_DOWNLOAD)

    await refresh_versions()


__all__ = ["render_versions_tab"]
