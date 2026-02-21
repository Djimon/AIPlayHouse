"""Desktop launcher for local host/player UI using PyWebView."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

from urllib import error, request

ROOT_DIR = Path(__file__).resolve().parents[2]
UI_FILE = ROOT_DIR / "dndtracker" / "client" / "ui" / "index.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DND Tracker launcher")
    parser.add_argument("--role", choices=["host", "player"], required=True)
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--encounter-id", default="")
    parser.add_argument("--token", default="")
    parser.add_argument("--start-server", action="store_true")
    return parser.parse_args()


def wait_for_server(server_url: str, timeout_s: float = 8.0) -> bool:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            with request.urlopen(f"{server_url}/docs", timeout=0.5) as response:
                if int(response.status) < 500:
                    return True
        except (error.URLError, TimeoutError):
            pass
        time.sleep(0.2)
    return False


def maybe_start_server(server_url: str) -> subprocess.Popen[str] | None:
    env = os.environ.copy()
    host_port = server_url.removeprefix("http://")
    host, port = host_port.split(":", maxsplit=1)
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "dndtracker.backend.api:app",
        "--host",
        host,
        "--port",
        port,
    ]
    process = subprocess.Popen(command, cwd=str(ROOT_DIR), env=env)
    if wait_for_server(server_url):
        return process
    process.terminate()
    return None


def build_ui_url(role: str, server: str, encounter_id: str, token: str) -> str:
    query = urlencode(
        {
            "role": role,
            "server": server,
            "encounter_id": encounter_id,
            "token": token,
        }
    )
    return f"file://{UI_FILE}?{query}"


def open_ui(url: str, title: str) -> None:
    try:
        import webview

        webview.create_window(title, url=url, width=1280, height=860)
        webview.start()
    except Exception:
        webbrowser.open(url)


def main() -> int:
    args = parse_args()

    server_process: subprocess.Popen[str] | None = None
    if args.start_server:
        server_process = maybe_start_server(args.server)
        if server_process is None:
            print("Server konnte nicht gestartet werden.", file=sys.stderr)
            return 1
    elif not wait_for_server(args.server):
        print("Server nicht erreichbar. Starte mit --start-server oder uvicorn manuell.", file=sys.stderr)
        return 1

    title = f"DND Tracker - {args.role.upper()}"
    url = build_ui_url(
        role=args.role.upper(),
        server=args.server,
        encounter_id=args.encounter_id,
        token=args.token,
    )
    try:
        open_ui(url=url, title=title)
    finally:
        if server_process is not None:
            server_process.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
