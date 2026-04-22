"""
File storage service — handles streaming upload and retrieval of .tar.gz packages.

Files are written in 1 MB chunks (``shutil.copyfileobj`` equivalent) to keep
memory usage bounded regardless of file size.  A partial file is cleaned up on
any I/O error.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from fastapi import UploadFile

from backend.config import CONFIG
from backend.services.audit_logger import append_log
from backend.services.project_service import get_project_dir

logger = logging.getLogger(__name__)

_MAX_FILE_SIZE: int = CONFIG["MAX_FILE_SIZE"]
_CHUNK_SIZE: int = 1024 * 1024  # 1 MB


async def save_version_file(
    project_name: str,
    version: str,
    file: UploadFile,
    username: str,
    about: str = "",
) -> dict:
    """
    Stream *file* to ``/data/project/{project_name}/{version}/{timestamp}.tar.gz``.

    Raises:
        ValueError: if the file exceeds MAX_FILE_SIZE.
        OSError: on I/O failures (partial file is removed automatically).
    """
    project_dir = get_project_dir(project_name)
    version_dir = os.path.join(project_dir, version)
    os.makedirs(version_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    dest_path = os.path.join(version_dir, f"{timestamp}.tar.gz")
    file_name = os.path.basename(dest_path)

    written = 0
    try:
        with open(dest_path, "wb") as dest:
            while True:
                chunk = await file.read(_CHUNK_SIZE)
                if not chunk:
                    break
                written += len(chunk)
                if written > _MAX_FILE_SIZE:
                    raise ValueError(
                        f"File exceeds the {_MAX_FILE_SIZE // (1024 * 1024)} MB size limit"
                    )
                dest.write(chunk)
    except Exception:
        if os.path.exists(dest_path):
            os.unlink(dest_path)
        raise

    about_path = os.path.join(version_dir, "about.md")
    with open(about_path, "w", encoding="utf-8") as about_fh:
        about_fh.write((about or "").strip() + "\n" if (about or "").strip() else "")

    log_file = os.path.join(project_dir, "project_history.txt")
    append_log(
        log_file,
        username,
        "UPLOAD_VERSION",
        f"{project_name}/{version}/{file_name} ({written} bytes) about_len={len((about or '').strip())}",
    )

    logger.info("Saved %d bytes → %s", written, dest_path)
    return {
        "project": project_name,
        "version": version,
        "path": f"/data/project/{project_name}/{version}/{file_name}",
        "size": written,
        "about": (about or "").strip(),
    }


def get_version_file_path(project_name: str, version: str) -> str:
    """
    Return the most recent .tar.gz file path for the given *version*.

    Raises FileNotFoundError if the version directory or its files are absent.
    """
    project_dir = get_project_dir(project_name)
    version_dir = os.path.join(project_dir, version)

    if not os.path.isdir(version_dir):
        raise FileNotFoundError(
            f"Version '{version}' not found in project '{project_name}'"
        )

    files = sorted(
        [f for f in os.listdir(version_dir) if f.endswith(".tar.gz")],
        reverse=True,
    )
    if not files:
        raise FileNotFoundError(f"No .tar.gz file found for version '{version}'")

    return os.path.join(version_dir, files[0])
