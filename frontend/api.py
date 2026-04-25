"""
HTTP helper — thin httpx wrapper that injects the JWT bearer token.
"""
from __future__ import annotations

import json as _json
from typing import Optional

import httpx
from nicegui import ui

from frontend.auth import get_token
from frontend.config import BACKEND_PORT, BACKEND_URL


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
    headers: dict[str, str] = {}
    tok = get_token()
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


def open_download(project_name: str, version: str) -> None:
    """Open the file-download URL for a specific project version in a new tab."""
    token = get_token()
    if not token:
        ui.notify("Not authenticated", type="negative")
        ui.navigate.to("/login")
        return

    ui.run_javascript(
        f"""
        const projectName = {_json.dumps(project_name)};
        const version = {_json.dumps(version)};
        const token = {_json.dumps(token)};
        const url = new URL(window.location.href);
        url.protocol = window.location.protocol;
        url.hostname = window.location.hostname;
        url.port = {_json.dumps(str(BACKEND_PORT))};
        url.pathname = `/projects/${{encodeURIComponent(projectName)}}/versions/${{encodeURIComponent(version)}}/download`;
        url.search = `token=${{encodeURIComponent(token)}}`;
        window.open(url.toString(), "_blank");
        """
    )


__all__ = ["api", "open_download"]
