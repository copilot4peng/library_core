"""Run backend and frontend in one container."""
from __future__ import annotations

import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable
COMMANDS = {
    "backend": [PYTHON, "-m", "backend.main"],
    "frontend": [PYTHON, "-m", "frontend.app"],
}

_BACKEND_HEALTH_URL = "http://127.0.0.1:8000/health"
_HEALTH_TIMEOUT = 30  # seconds to wait for backend before giving up


def _wait_for_backend(proc: subprocess.Popen, timeout: int = _HEALTH_TIMEOUT) -> bool:
    """Poll /health until the backend responds or the process dies."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False  # backend exited prematurely
        try:
            with urllib.request.urlopen(_BACKEND_HEALTH_URL, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def terminate(processes: dict[str, subprocess.Popen], sig: int) -> None:
    for process in processes.values():
        if process.poll() is None:
            process.send_signal(sig)


def wait_for_exit(processes: dict[str, subprocess.Popen]) -> int:
    while True:
        for name, process in processes.items():
            exit_code = process.poll()
            if exit_code is not None:
                print(f"{name} exited with code {exit_code}; stopping remaining services.", flush=True)
                terminate(processes, signal.SIGTERM)
                time.sleep(1)
                terminate(processes, signal.SIGKILL)
                for remaining in processes.values():
                    try:
                        remaining.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        pass
                return exit_code
        time.sleep(0.5)


def main() -> int:
    backend = subprocess.Popen(COMMANDS["backend"], cwd=ROOT)
    print("Waiting for backend to become healthy…", flush=True)
    if not _wait_for_backend(backend):
        print("Backend failed to start. Aborting.", flush=True)
        backend.kill()
        return 1

    print("Backend healthy — starting frontend.", flush=True)
    frontend = subprocess.Popen(COMMANDS["frontend"], cwd=ROOT)
    processes = {"backend": backend, "frontend": frontend}

    def handle_signal(signum, _frame) -> None:
        terminate(processes, signum)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    return wait_for_exit(processes)


if __name__ == "__main__":
    raise SystemExit(main())