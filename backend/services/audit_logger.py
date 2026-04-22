"""
Thread- and process-safe append-only audit logger.

Each entry is a pipe-delimited line::

    <ISO-8601 UTC timestamp>|<username>|<action>|<detail>

File writes are protected by an exclusive ``portalocker`` lock so concurrent
processes never corrupt ``project_history.txt``.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import portalocker

logger = logging.getLogger(__name__)


def append_log(log_file: str, username: str, action: str, detail: str = "") -> None:
    """Append one audit entry to *log_file* under an exclusive file lock."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = f"{timestamp}|{username}|{action}|{detail}\n"

    with open(log_file, "a", encoding="utf-8") as fh:
        portalocker.lock(fh, portalocker.LOCK_EX)
        try:
            fh.write(entry)
            fh.flush()
        finally:
            portalocker.unlock(fh)

    logger.debug("Audit: %s", entry.rstrip())


def read_logs(log_file: str) -> list[str]:
    """Return all non-empty log lines, protected by a shared read lock."""
    if not os.path.exists(log_file):
        return []

    with open(log_file, "r", encoding="utf-8") as fh:
        portalocker.lock(fh, portalocker.LOCK_SH)
        try:
            lines = fh.readlines()
        finally:
            portalocker.unlock(fh)

    return [line.rstrip("\n") for line in lines if line.strip()]
