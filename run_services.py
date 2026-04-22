"""Run backend and frontend in one container."""
from __future__ import annotations

import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable
COMMANDS = {
    "backend": [PYTHON, "-m", "backend.main"],
    "frontend": [PYTHON, "-m", "frontend.app"],
}


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
    processes = {
        name: subprocess.Popen(command, cwd=ROOT)
        for name, command in COMMANDS.items()
    }

    def handle_signal(signum, _frame) -> None:
        terminate(processes, signum)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    return wait_for_exit(processes)


if __name__ == "__main__":
    raise SystemExit(main())