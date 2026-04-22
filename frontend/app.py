"""
MyBagHub — NiceGUI frontend.

Pages
-----
/               → redirect to /login or /projects
/login          → Login form
/register       → Registration form
/projects       → Project list + create
/projects/{name}→ Versions, audit log, members management

Run:
    python -m frontend.app
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Optional

import httpx
from nicegui import app, ui
from nicegui.events import UploadEventArguments

# Allow importing backend.config when running both services from the same repo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import CONFIG  # noqa: E402

logger = logging.getLogger("mybagHub.frontend")

BACKEND_URL: str = CONFIG.get("BACKEND_URL", "http://localhost:8000")


# ─────────────────────────────────────────────────────────────────────────────
# Session helpers
# ─────────────────────────────────────────────────────────────────────────────

def _token() -> Optional[str]:
    return app.storage.user.get("token")


def _username() -> Optional[str]:
    return app.storage.user.get("username")


def _is_auth() -> bool:
    return bool(_token())


def _logout() -> None:
    app.storage.user.clear()
    ui.navigate.to("/login")


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _api(
    method: str,
    path: str,
    *,
    json: Optional[dict] = None,
    data: Optional[dict] = None,
    files: Optional[dict] = None,
    params: Optional[dict] = None,
    timeout: float = 300.0,
) -> httpx.Response:
    """Thin wrapper around httpx that injects the JWT token."""
    headers: dict[str, str] = {}
    tok = _token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"

    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.request(
            method,
            f"{BACKEND_URL}{path}",
            headers=headers,
            json=json,
            data=data,
            files=files,
            params=params,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Reusable header
# ─────────────────────────────────────────────────────────────────────────────

def _nav_header(subtitle: str = "") -> None:
    with ui.header().classes("bg-blue-700 text-white items-center px-6 py-3 gap-4"):
        ui.label("📦 MyBagHub").classes(
            "text-xl font-bold cursor-pointer"
        ).on("click", lambda: ui.navigate.to("/projects"))
        if subtitle:
            ui.label(f"/ {subtitle}").classes("text-lg opacity-75")
        ui.space()
        user = _username()
        if user:
            ui.label(user).classes("text-sm opacity-80 mr-2")
        ui.button("Logout", on_click=_logout).props("flat").classes(
            "text-white border border-white"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Root  /
# ─────────────────────────────────────────────────────────────────────────────

@ui.page("/")
async def root_page() -> None:
    if _is_auth():
        ui.navigate.to("/projects")
    else:
        ui.navigate.to("/login")


# ─────────────────────────────────────────────────────────────────────────────
# /login
# ─────────────────────────────────────────────────────────────────────────────

@ui.page("/login")
async def login_page() -> None:
    if _is_auth():
        ui.navigate.to("/projects")
        return

    with ui.card().classes("absolute-center w-96 shadow-lg p-6"):
        ui.label("📦 MyBagHub").classes("text-2xl font-bold text-center mb-6")

        username_in = ui.input("Username").classes("w-full")
        password_in = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")
        error_lbl = ui.label("").classes("text-red-500 text-sm min-h-4")

        async def do_login() -> None:
            error_lbl.set_text("")
            u, p = username_in.value.strip(), password_in.value
            if not u or not p:
                error_lbl.set_text("Please enter username and password")
                return
            try:
                resp = await _api("POST", "/auth/login", json={"username": u, "password": p})
            except httpx.RequestError:
                error_lbl.set_text("Cannot reach the backend — check BACKEND_URL in config.json")
                return

            if resp.status_code == 200:
                data = resp.json()
                app.storage.user["token"] = data["access_token"]
                app.storage.user["username"] = u
                ui.navigate.to("/projects")
            else:
                error_lbl.set_text(resp.json().get("detail", "Login failed"))

        ui.button("Login", on_click=do_login).classes("w-full mt-3 bg-blue-600 text-white")

        with ui.row().classes("w-full justify-center mt-3 gap-1 text-sm"):
            ui.label("No account?")
            ui.link("Register here", "/register")


# ─────────────────────────────────────────────────────────────────────────────
# /register
# ─────────────────────────────────────────────────────────────────────────────

@ui.page("/register")
async def register_page() -> None:
    if _is_auth():
        ui.navigate.to("/projects")
        return

    with ui.card().classes("absolute-center w-96 shadow-lg p-6"):
        ui.label("Create Account").classes("text-2xl font-bold text-center mb-6")

        username_in = ui.input("Username").classes("w-full")
        password_in = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")
        confirm_in = ui.input("Confirm Password", password=True, password_toggle_button=True).classes("w-full")
        error_lbl = ui.label("").classes("text-red-500 text-sm min-h-4")

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
                resp = await _api("POST", "/auth/register", json={"username": u, "password": p})
            except httpx.RequestError:
                error_lbl.set_text("Cannot reach the backend")
                return

            if resp.status_code == 201:
                ui.notify("Registration successful — please log in", type="positive")
                ui.navigate.to("/login")
            else:
                error_lbl.set_text(resp.json().get("detail", "Registration failed"))

        ui.button("Register", on_click=do_register).classes("w-full mt-3 bg-blue-600 text-white")

        with ui.row().classes("w-full justify-center mt-3 gap-1 text-sm"):
            ui.label("Already have an account?")
            ui.link("Log in", "/login")


# ─────────────────────────────────────────────────────────────────────────────
# /projects
# ─────────────────────────────────────────────────────────────────────────────

@ui.page("/projects")
async def projects_page() -> None:
    if not _is_auth():
        ui.navigate.to("/login")
        return

    _nav_header()

    with ui.column().classes("w-full max-w-4xl mx-auto p-6 gap-6"):
        ui.label("My Projects").classes("text-2xl font-bold")

        # ── Create project card ───────────────────────────────────────────────
        with ui.card().classes("w-full p-4"):
            ui.label("Create New Project").classes("text-lg font-semibold mb-2")
            name_in = ui.input("Project name (letters, digits, _ -)").classes("w-full")
            create_err = ui.label("").classes("text-red-500 text-sm min-h-4")

            async def do_create() -> None:
                create_err.set_text("")
                name = name_in.value.strip()
                if not name:
                    create_err.set_text("Name cannot be empty")
                    return
                resp = await _api("POST", "/projects", json={"name": name})
                if resp.status_code == 201:
                    ui.notify(f"Project '{name}' created", type="positive")
                    name_in.set_value("")
                    await refresh()
                else:
                    create_err.set_text(resp.json().get("detail", "Failed to create project"))

            ui.button("Create", on_click=do_create).classes("mt-2 bg-blue-600 text-white")

        # ── Projects list ─────────────────────────────────────────────────────
        list_area = ui.column().classes("w-full gap-3")

        async def refresh() -> None:
            list_area.clear()
            resp = await _api("GET", "/projects")
            if resp.status_code != 200:
                with list_area:
                    ui.label("Failed to load projects").classes("text-red-500")
                return

            items: list[dict] = resp.json().get("data", [])
            with list_area:
                if not items:
                    ui.label("No projects yet — create one above.").classes(
                        "text-gray-400 italic"
                    )
                    return
                for proj in items:
                    pname = proj["name"]
                    with ui.card().classes(
                        "w-full p-4 flex flex-row items-center justify-between hover:shadow-md transition-shadow"
                    ):
                        with ui.column().classes("gap-0"):
                            ui.label(pname).classes("text-lg font-semibold")
                            ui.label(f"Owner: {proj['owner']}").classes(
                                "text-sm text-gray-500"
                            )
                            members = proj.get("users", [])
                            if len(members) > 1:
                                ui.label(f"Members: {', '.join(members)}").classes(
                                    "text-xs text-gray-400"
                                )
                        ui.button(
                            "Open →",
                            on_click=lambda p=pname: ui.navigate.to(f"/projects/{p}"),
                        ).classes("bg-blue-500 text-white")

        await refresh()


# ─────────────────────────────────────────────────────────────────────────────
# /projects/{name}
# ─────────────────────────────────────────────────────────────────────────────

@ui.page("/projects/{name}")
async def project_detail_page(name: str) -> None:
    if not _is_auth():
        ui.navigate.to("/login")
        return

    _nav_header(subtitle=name)

    with ui.column().classes("w-full max-w-5xl mx-auto p-6 gap-4"):
        ui.label(f"Project: {name}").classes("text-2xl font-bold")

        with ui.tabs().classes("w-full") as tabs:
            tab_versions = ui.tab("Versions")
            tab_logs = ui.tab("Audit Log")
            tab_members = ui.tab("Members")

        with ui.tab_panels(tabs, value=tab_versions).classes("w-full"):

            # ══ Versions tab ═════════════════════════════════════════════════
            with ui.tab_panel(tab_versions):

                # ── Upload section ────────────────────────────────────────
                with ui.card().classes("w-full p-4 mb-4"):
                    ui.label("Upload New Version").classes("text-lg font-semibold mb-3")

                    version_in = ui.input(
                        "Version tag (e.g. v1.0 or v2.3.1)"
                    ).classes("w-full")
                    about_in = ui.textarea("Version description (optional)").classes(
                        "w-full"
                    ).props("autogrow")

                    pending: dict = {}  # {"data": bytes, "name": str}
                    file_status = ui.label("No file selected").classes(
                        "text-sm text-gray-500 mt-1"
                    )
                    upload_msg = ui.label("").classes("text-sm min-h-4")

                    async def on_file_received(e: UploadEventArguments) -> None:
                        # NiceGUI 3.x exposes uploaded file via e.file (async read API).
                        try:
                            data = await e.file.read()
                            name = e.file.name
                        except Exception as exc:
                            logger.exception("Failed to read uploaded file content")
                            pending.clear()
                            file_status.set_text("No file selected")
                            file_status.classes(remove="text-green-600", add="text-gray-500")
                            upload_msg.set_text(f"Failed to process selected file: {exc}")
                            upload_msg.classes(remove="text-green-600", add="text-red-500")
                            return

                        if not data:
                            pending.clear()
                            file_status.set_text("No file selected")
                            file_status.classes(remove="text-green-600", add="text-gray-500")
                            upload_msg.set_text("Selected file is empty or could not be read")
                            upload_msg.classes(remove="text-green-600", add="text-red-500")
                            return

                        pending["data"] = data
                        pending["name"] = name
                        size_kb = len(data) / 1024
                        file_status.set_text(
                            f"Selected: {name}  ({size_kb:,.1f} KB)"
                        )
                        file_status.classes(remove="text-gray-500", add="text-green-600")
                        upload_msg.set_text("File selected, ready to upload")
                        upload_msg.classes(remove="text-red-500 text-blue-500", add="text-green-600")

                    def on_file_rejected() -> None:
                        pending.clear()
                        file_status.set_text("No file selected")
                        file_status.classes(remove="text-green-600", add="text-gray-500")
                        max_mb = CONFIG.get("MAX_FILE_SIZE", 0) / (1024 * 1024)
                        upload_msg.set_text(
                            f"File rejected by browser/uploader. Limit: {max_mb:.0f} MB"
                        )
                        upload_msg.classes(remove="text-green-600 text-blue-500", add="text-red-500")

                    ui.upload(
                        label="Drop .tar.gz file here (or click)",
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
                            upload_msg.classes(remove="text-green-600", add="text-red-500")
                            return
                        if not pending.get("data"):
                            upload_msg.set_text("Please select a .tar.gz file first")
                            upload_msg.classes(remove="text-green-600", add="text-red-500")
                            return

                        upload_msg.set_text("Uploading…")
                        upload_msg.classes(remove="text-red-500 text-green-600", add="text-blue-500")

                        file_tuple = (pending["name"], pending["data"], "application/gzip")
                        try:
                            resp = await _api(
                                "POST",
                                f"/projects/{name}/versions",
                                files={"file": file_tuple},
                                data={
                                    "version": ver,
                                    "about": about_in.value.strip(),
                                },
                            )
                        except httpx.RequestError:
                            upload_msg.set_text("Network error — upload failed")
                            upload_msg.classes(remove="text-blue-500", add="text-red-500")
                            return

                        if resp.status_code == 200:
                            upload_msg.set_text(
                                f"✓ Uploaded {pending['name']} as {ver}"
                            )
                            upload_msg.classes(
                                remove="text-red-500 text-blue-500", add="text-green-600"
                            )
                            pending.clear()
                            file_status.set_text("No file selected")
                            file_status.classes(remove="text-green-600", add="text-gray-500")
                            version_in.set_value("")
                            about_in.set_value("")
                            await refresh_versions()
                        else:
                            detail = resp.json().get("detail", "Upload failed")
                            upload_msg.set_text(detail)
                            upload_msg.classes(
                                remove="text-blue-500 text-green-600", add="text-red-500"
                            )

                    ui.button("Upload Version", on_click=do_upload).classes(
                        "mt-3 bg-blue-600 text-white"
                    )

                # ── Version list ──────────────────────────────────────────
                versions_area = ui.column().classes("w-full gap-2")

                async def refresh_versions() -> None:
                    versions_area.clear()
                    resp = await _api("GET", f"/projects/{name}/versions")
                    if resp.status_code != 200:
                        with versions_area:
                            ui.label("Failed to load versions").classes("text-red-500")
                        return

                    items: list[dict] = resp.json().get("data", [])
                    with versions_area:
                        if not items:
                            ui.label("No versions uploaded yet.").classes(
                                "text-gray-400 italic"
                            )
                            return
                        for v in items:
                            ver_tag = v["version"]
                            fname = v["file_name"]
                            size_mb = v.get("size", 0) / (1024 * 1024)
                            uploaded = v["upload_at"][:19].replace("T", " ")
                            about = (v.get("about") or "").strip()

                            dl_url = (
                                f"{BACKEND_URL}/projects/{name}/versions/{ver_tag}"
                                f"/download?token={_token()}"
                            )

                            with ui.card().classes("w-full p-3"):
                                with ui.row().classes(
                                    "w-full items-center justify-between"
                                ):
                                    with ui.column().classes("gap-0"):
                                        ui.label(ver_tag).classes("font-semibold text-base")
                                        ui.label(fname).classes("text-sm text-gray-500")
                                        ui.label(
                                            f"{size_mb:.2f} MB  ·  {uploaded} UTC"
                                        ).classes("text-xs text-gray-400")
                                        if about:
                                            ui.markdown(about).classes("text-sm mt-2")

                                    ui.button(
                                        "⬇ Download",
                                        on_click=lambda u=dl_url: ui.run_javascript(
                                            f'window.open("{u}", "_blank")'
                                        ),
                                    ).classes("bg-green-600 text-white")

                await refresh_versions()

            # ══ Audit Log tab ═════════════════════════════════════════════
            with ui.tab_panel(tab_logs):
                logs_area = ui.column().classes("w-full gap-1")

                async def load_logs() -> None:
                    logs_area.clear()
                    resp = await _api("GET", f"/projects/{name}/logs")
                    if resp.status_code != 200:
                        with logs_area:
                            ui.label("Failed to load audit log").classes("text-red-500")
                        return

                    entries: list[str] = resp.json().get("data", [])
                    with logs_area:
                        if not entries:
                            ui.label("No audit entries yet.").classes(
                                "text-gray-400 italic"
                            )
                            return

                        # Show newest first
                        for line in reversed(entries):
                            parts = line.split("|", 3)
                            if len(parts) == 4:
                                ts, user, action, detail = parts
                                with ui.card().classes(
                                    "w-full p-2 font-mono text-xs"
                                ):
                                    with ui.row().classes("gap-3 items-center flex-wrap"):
                                        ui.label(ts).classes("text-gray-400 w-32")
                                        ui.label(user).classes("font-bold w-24")
                                        ui.label(action).classes(
                                            "text-blue-600 w-36"
                                        )
                                        ui.label(detail).classes("text-gray-600")
                            else:
                                ui.label(line).classes("font-mono text-xs text-gray-500")

                await load_logs()

            # ══ Members tab ═══════════════════════════════════════════════
            with ui.tab_panel(tab_members):
                members_area = ui.column().classes("w-full gap-3")

                async def load_members() -> None:
                    members_area.clear()
                    resp = await _api("GET", "/projects")
                    if resp.status_code != 200:
                        with members_area:
                            ui.label("Failed to load project info").classes(
                                "text-red-500"
                            )
                        return

                    all_projects: list[dict] = resp.json().get("data", [])
                    proj_info = next(
                        (p for p in all_projects if p["name"] == name), None
                    )
                    if proj_info is None:
                        with members_area:
                            ui.label("Project not found").classes("text-red-500")
                        return

                    with members_area:
                        ui.label("Current Members").classes("text-lg font-semibold")
                        for member in proj_info["users"]:
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("person")
                                ui.label(member)
                                if member == proj_info["owner"]:
                                    ui.badge("Owner").classes(
                                        "bg-blue-100 text-blue-700"
                                    )

                        # Only the owner can add members
                        if proj_info["owner"] == _username():
                            ui.separator().classes("my-4")
                            ui.label("Add Member").classes("text-lg font-semibold")
                            new_user_in = ui.input(
                                "Username to add"
                            ).classes("w-full max-w-xs")
                            add_err = ui.label("").classes("text-red-500 text-sm min-h-4")

                            async def do_add_member() -> None:
                                add_err.set_text("")
                                nu = new_user_in.value.strip()
                                if not nu:
                                    add_err.set_text("Enter a username")
                                    return
                                resp2 = await _api(
                                    "POST",
                                    f"/projects/{name}/users",
                                    params={"username": nu},
                                )
                                if resp2.status_code == 200:
                                    ui.notify(
                                        f"'{nu}' added to project", type="positive"
                                    )
                                    new_user_in.set_value("")
                                    await load_members()
                                else:
                                    add_err.set_text(
                                        resp2.json().get("detail", "Failed to add member")
                                    )

                            ui.button("Add Member", on_click=do_add_member).classes(
                                "mt-2 bg-blue-600 text-white"
                            )

                await load_members()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host=CONFIG.get("FRONTEND_HOST", "0.0.0.0"),
        port=int(CONFIG.get("FRONTEND_PORT", 8080)),
        title="MyBagHub",
        storage_secret=CONFIG.get("JWT_SECRET", "nicegui-fallback-secret"),
        show=False,
        reload=False,
    )
