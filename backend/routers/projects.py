"""Project management and file-version endpoints."""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from backend.dependencies import get_current_user, get_current_user_query_token
from backend.schemas import ProjectCreateRequest
from backend.services import audit_logger, file_service, project_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])

# Allowed version format: v1, v1.0, v1.2.3, v1.0.0-beta.1, etc.
_VERSION_RE = re.compile(r"^v\d+(\.\d+){0,2}([-+][\w.]+)?$")


# ── Guards ────────────────────────────────────────────────────────────────────

def _require_access(project_name: str, username: str) -> None:
    """Raise 404 / 403 if the project is absent or *username* is not a member."""
    if not project_service.project_exists(project_name):
        raise HTTPException(status_code=404, detail="Project not found")
    if not project_service.is_project_member(project_name, username):
        raise HTTPException(
            status_code=403, detail="You do not have access to this project"
        )


# ── Project endpoints ─────────────────────────────────────────────────────────

@router.get("", summary="List projects the current user belongs to")
async def list_projects(current_user: str = Depends(get_current_user)):
    data = project_service.list_projects(current_user)
    return {"status": "success", "data": data}


@router.post("", status_code=201, summary="Create a new project")
async def create_project(
    req: ProjectCreateRequest,
    current_user: str = Depends(get_current_user),
):
    try:
        project = project_service.create_project(req.name, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "success", "data": project}


@router.post("/{name}/users", summary="Add a member to a project (owner only)")
async def add_project_member(
    name: str,
    username: str = Query(..., description="Username to add"),
    current_user: str = Depends(get_current_user),
):
    if not project_service.project_exists(name):
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        project_service.add_project_user(name, username, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"status": "success", "message": f"User '{username}' added to '{name}'"}


# ── Version endpoints ─────────────────────────────────────────────────────────

@router.get("/{name}/versions", summary="List all uploaded versions")
async def list_versions(
    name: str,
    current_user: str = Depends(get_current_user),
):
    _require_access(name, current_user)
    data = project_service.list_versions(name)
    return {"status": "success", "data": data}


@router.post("/{name}/versions", summary="Upload a new version (.tar.gz)")
async def upload_version(
    name: str,
    version: Optional[str] = Query(None, description="Version tag, e.g. v1.0"),
    version_form: Optional[str] = Form(None, alias="version"),
    about: str = Form(""),
    file: UploadFile = File(...),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    current_user: str = Depends(get_current_user),
):
    _require_access(name, current_user)

    resolved_version = (version_form or version or "").strip()
    if not resolved_version:
        raise HTTPException(status_code=400, detail="Missing version")

    if not _VERSION_RE.match(resolved_version):
        raise HTTPException(
            status_code=400,
            detail="Invalid version format. Use semver-like tags, e.g. v1.0 or v2.3.1-beta",
        )

    original_name = file.filename or ""
    if not original_name.endswith(".tar.gz"):
        raise HTTPException(status_code=400, detail="Only .tar.gz files are accepted")

    try:
        result = await file_service.save_version_file(
            name,
            resolved_version,
            file,
            current_user,
            about=about,
        )
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    return {"status": "success", "data": result}


@router.get(
    "/{name}/versions/{version}/download",
    summary="Download the latest .tar.gz for a version",
)
async def download_version(
    name: str,
    version: str,
    current_user: str = Depends(get_current_user_query_token),
):
    _require_access(name, current_user)

    try:
        file_path = file_service.get_version_file_path(name, version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    project_dir = project_service.get_project_dir(name)
    audit_logger.append_log(
        os.path.join(project_dir, "project_history.txt"),
        current_user,
        "DOWNLOAD_VERSION",
        f"{name}/{version}",
    )

    return FileResponse(
        file_path,
        media_type="application/gzip",
        filename=os.path.basename(file_path),
    )


# ── Logs endpoint ─────────────────────────────────────────────────────────────

@router.get("/{name}/logs", summary="Read the project audit log")
async def get_project_logs(
    name: str,
    current_user: str = Depends(get_current_user),
):
    _require_access(name, current_user)
    log_file = os.path.join(project_service.get_project_dir(name), "project_history.txt")
    entries = audit_logger.read_logs(log_file)
    return {"status": "success", "data": entries}
