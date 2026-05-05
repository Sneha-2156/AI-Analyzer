from __future__ import annotations

import os
import subprocess
from pathlib import Path

import uvicorn

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def build_frontend() -> None:
    if os.getenv("SKIP_FRONTEND_BUILD") == "1":
        return
    _run(["npm", "run", "build"], cwd=FRONTEND_DIR)


def start_api() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload_enabled = os.getenv("RELOAD") == "1"
    uvicorn.run("app.main:app", host=host, port=port, reload=reload_enabled, app_dir=str(BACKEND_DIR))


if __name__ == "__main__":
    build_frontend()
    start_api()
