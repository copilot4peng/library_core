"""
File-system backed user authentication service.

Directory layout::

    /data/user/
        {username}/
            password_hash.txt   # bcrypt hash, chmod 600
            status.txt          # "online" | "offline"

All input validation is performed at the Pydantic schema layer; only
existence/format checks happen here.
"""
from __future__ import annotations

import logging
import os

import bcrypt

from backend.config import CONFIG

logger = logging.getLogger(__name__)

_USER_ROOT = os.path.join(CONFIG["STORAGE_ROOT"], "user")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _user_dir(username: str) -> str:
    """Return the absolute path to a user's directory (not validated here)."""
    return os.path.join(_USER_ROOT, username)


def _safe_user_dir(username: str) -> str:
    """
    Return the user directory path after verifying it stays within _USER_ROOT.
    Raises ValueError on path-traversal attempts.
    """
    base = os.path.realpath(_USER_ROOT)
    target = os.path.realpath(os.path.join(_USER_ROOT, username))
    if not target.startswith(base + os.sep) and target != base:
        raise ValueError("Invalid username — path traversal detected")
    return target


# ── Public API ────────────────────────────────────────────────────────────────

def user_exists(username: str) -> bool:
    return os.path.isdir(_user_dir(username))


def register_user(username: str, password: str) -> None:
    """
    Create a new user directory, storing a bcrypt hash of *password*.
    Raises ValueError if the user already exists.
    """
    user_dir = _safe_user_dir(username)

    if os.path.isdir(user_dir):
        raise ValueError("User already exists")

    os.makedirs(user_dir, exist_ok=True)

    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    hash_file = os.path.join(user_dir, "password_hash.txt")
    with open(hash_file, "w", encoding="utf-8") as fh:
        fh.write(pw_hash)
    # Restrict read access to the owning process only
    os.chmod(hash_file, 0o600)

    with open(os.path.join(user_dir, "status.txt"), "w", encoding="utf-8") as fh:
        fh.write("offline")

    logger.info("Registered user '%s'", username)


def verify_password(username: str, password: str) -> bool:
    """
    Verify *password* against the stored bcrypt hash.
    Always performs a hash check (even for unknown users) to prevent
    timing-based user enumeration.
    """
    if not user_exists(username):
        # Constant-time dummy check
        bcrypt.checkpw(b"dummy", bcrypt.hashpw(b"dummy", bcrypt.gensalt()))
        return False

    hash_file = os.path.join(_user_dir(username), "password_hash.txt")
    try:
        with open(hash_file, "r", encoding="utf-8") as fh:
            stored = fh.read().strip()
        return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
    except (OSError, ValueError):
        logger.exception("Could not read password hash for '%s'", username)
        return False


def set_user_status(username: str, status: str) -> None:
    status_file = os.path.join(_user_dir(username), "status.txt")
    with open(status_file, "w", encoding="utf-8") as fh:
        fh.write(status)


def get_user_status(username: str) -> str:
    status_file = os.path.join(_user_dir(username), "status.txt")
    if not os.path.exists(status_file):
        return "offline"
    with open(status_file, "r", encoding="utf-8") as fh:
        return fh.read().strip()
