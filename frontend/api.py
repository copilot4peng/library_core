"""
HTTP helper — thin httpx wrapper that injects the JWT bearer token.

The backend URL is not fixed at startup; it is stored in the user's browser
session after they select a server on the /server page.
"""
from __future__ import annotations

import json as _json
from typing import Optional

import httpx
from nicegui import ui

from frontend.auth import get_server_url, get_token


async def api(
    method: str,
    path: str,
    *,
    json: Optional[dict] = None,
    data: Optional[dict] = None,
    files: Optional[dict] = None,
    params: Optional[dict] = None,
    timeout: float = 300.0,
) -> httpx.Response:
    """Execute an HTTP request against the backend, injecting the JWT token."""
    server_url = get_server_url()
    if not server_url:
        raise RuntimeError("No backend server configured — please select a server first")

    headers: dict[str, str] = {}
    tok = get_token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"

    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.request(
            method,
            f"{server_url}{path}",
            headers=headers,
            json=json,
            data=data,
            files=files,
            params=params,
        )


def open_download(project_name: str, version: str) -> None:
    """Open the file-download URL for a specific project version in a new tab.

    The server URL comes from the session (entered by the user), so it is
    always the browser-visible address — no Docker-internal leakage.
    """
    token = get_token()
    if not token:
        ui.notify("Not authenticated", type="negative")
        ui.navigate.to("/login")
        return

    server_url = get_server_url()
    if not server_url:
        ui.notify("No server configured", type="negative")
        ui.navigate.to("/server")
        return

    ui.run_javascript(
        f"""
        const projectName = {_json.dumps(project_name)};
        const version = {_json.dumps(version)};
        const token = {_json.dumps(token)};
        const serverUrl = {_json.dumps(server_url)};
        const url = serverUrl
            + '/projects/' + encodeURIComponent(projectName)
            + '/versions/' + encodeURIComponent(version)
            + '/download?token=' + encodeURIComponent(token);
        window.open(url, '_blank');
        """
    )


__all__ = ["api", "open_download"]
