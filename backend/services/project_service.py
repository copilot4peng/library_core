"""
File-system backed project management service.

Directory layout::

    /data/project/
        {project_name}/
            owner.txt               # single username (project owner)
            users.txt               # one username per line (all members)
            project_history.txt     # append-only audit log
            {version}/              # e.g. v1.0/
                {timestamp}.tar.gz
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import portalocker

from backend.config import CONFIG
from backend.services.audit_logger import append_log

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.join(CONFIG["STORAGE_ROOT"], "project")


# ── Path helpers ──────────────────────────────────────────────────────────────

def get_project_dir(project_name: str) -> str:
    return os.path.join(_PROJECT_ROOT, project_name)


def _safe_project_dir(project_name: str) -> str:
    base = os.path.realpath(_PROJECT_ROOT)
    target = os.path.realpath(os.path.join(_PROJECT_ROOT, project_name))
    if not target.startswith(base + os.sep) and target != base:
        raise ValueError("Invalid project name — path traversal detected")
    return target


# ── Public API ────────────────────────────────────────────────────────────────

def project_exists(project_name: str) -> bool:
    return os.path.isdir(get_project_dir(project_name))


def create_project(project_name: str, owner: str) -> dict:
    """
    Create a new project directory with *owner.txt* and *users.txt*.
    Raises ValueError if the project already exists.
    """
    project_dir = _safe_project_dir(project_name)

    if os.path.isdir(project_dir):
        raise ValueError(f"Project '{project_name}' already exists")

    os.makedirs(project_dir, exist_ok=True)

    with open(os.path.join(project_dir, "owner.txt"), "w", encoding="utf-8") as fh:
        fh.write(owner)

    with open(os.path.join(project_dir, "users.txt"), "w", encoding="utf-8") as fh:
        fh.write(owner + "\n")

    log_file = os.path.join(project_dir, "project_history.txt")
    append_log(log_file, owner, "CREATE_PROJECT", project_name)

    logger.info("Created project '%s' (owner: %s)", project_name, owner)
    return {"name": project_name, "owner": owner, "users": [owner]}


def get_project_info(project_name: str) -> dict:
    project_dir = get_project_dir(project_name)

    with open(os.path.join(project_dir, "owner.txt"), encoding="utf-8") as fh:
        owner = fh.read().strip()

    users: list[str] = []
    users_file = os.path.join(project_dir, "users.txt")
    if os.path.exists(users_file):
        with open(users_file, encoding="utf-8") as fh:
            portalocker.lock(fh, portalocker.LOCK_SH)
            try:
                users = [u.strip() for u in fh.readlines() if u.strip()]
            finally:
                portalocker.unlock(fh)

    return {"name": project_name, "owner": owner, "users": users}


def list_projects(username: str | None = None) -> list[dict]:
    """Return all projects, optionally filtered to those *username* is a member of."""
    if not os.path.isdir(_PROJECT_ROOT):
        return []

    results: list[dict] = []
    for name in sorted(os.listdir(_PROJECT_ROOT)):
        if not os.path.isdir(os.path.join(_PROJECT_ROOT, name)):
            continue
        try:
            info = get_project_info(name)
            if username is None or username in info["users"]:
                results.append(info)
        except OSError as exc:
            logger.warning("Skipping project '%s': %s", name, exc)

    return results


def get_project_owner(project_name: str) -> str:
    with open(os.path.join(get_project_dir(project_name), "owner.txt"), encoding="utf-8") as fh:
        return fh.read().strip()


def is_project_member(project_name: str, username: str) -> bool:
    users_file = os.path.join(get_project_dir(project_name), "users.txt")
    if not os.path.exists(users_file):
        return False

    with open(users_file, encoding="utf-8") as fh:
        portalocker.lock(fh, portalocker.LOCK_SH)
        try:
            members = {u.strip() for u in fh.readlines() if u.strip()}
        finally:
            portalocker.unlock(fh)

    return username in members


def add_project_user(project_name: str, new_username: str, requester: str) -> None:
    """
    Add *new_username* to the project's member list.
    Only the project owner (*requester*) may perform this action.
    The operation is idempotent — adding an existing member is a no-op.
    """
    owner = get_project_owner(project_name)
    if requester != owner:
        raise PermissionError("Only the project owner can add members")

    users_file = os.path.join(get_project_dir(project_name), "users.txt")

    # Open in append+read mode and hold an exclusive lock for the full
    # read-check-write cycle, preventing TOCTOU races.
    with open(users_file, "a+", encoding="utf-8") as fh:
        portalocker.lock(fh, portalocker.LOCK_EX)
        try:
            fh.seek(0)
            existing = {u.strip() for u in fh.readlines() if u.strip()}
            if new_username not in existing:
                fh.seek(0, 2)  # seek to end
                fh.write(new_username + "\n")
        finally:
            portalocker.unlock(fh)

    log_file = os.path.join(get_project_dir(project_name), "project_history.txt")
    append_log(log_file, requester, "ADD_MEMBER", f"added {new_username}")
    logger.info("Added '%s' to project '%s' by '%s'", new_username, project_name, requester)


def list_versions(project_name: str) -> list[dict]:
    """Return metadata for every .tar.gz file found under version sub-directories."""
    project_dir = get_project_dir(project_name)
    versions: list[dict] = []

    for entry in sorted(os.listdir(project_dir)):
        entry_path = os.path.join(project_dir, entry)
        if not os.path.isdir(entry_path) or not entry.startswith("v"):
            continue

        about = ""
        about_file = os.path.join(entry_path, "about.md")
        if os.path.exists(about_file):
            with open(about_file, encoding="utf-8") as fh:
                about = fh.read().strip()

        for file_name in sorted(os.listdir(entry_path)):
            if not file_name.endswith(".tar.gz"):
                continue
            file_path = os.path.join(entry_path, file_name)
            stat = os.stat(file_path)
            versions.append(
                {
                    "version": entry,
                    "file_name": file_name,
                    "upload_at": datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(timespec="seconds"),
                    "size": stat.st_size,
                    "about": about,
                }
            )

    return versions
