"""Android bootstrap for the embedded Hermes Agent runtime.

This module is called from MainActivity through Chaquopy. It keeps Android
platform wiring separate from Hermes Agent code: filesystem layout, environment
variables, backend lifecycle, and small diagnostic commands live here, while
the real Agent/Gateway implementation remains the copied upstream source.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import threading
import time
import traceback
from typing import Any
from urllib.request import urlopen

_lock = threading.RLock()
_server_thread: threading.Thread | None = None
_server_port = 9129
_last_error = ""
_started_at = 0.0
_files_dir = ""


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _is_port_open(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _prepare_environment(files_dir: str) -> dict[str, str]:
    global _files_dir
    root = Path(files_dir).resolve()
    hermes_home = root / "hermes-home"
    workspace = hermes_home / "workspace"
    logs = hermes_home / "logs"
    for path in (hermes_home, workspace, logs):
        path.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("HOME", str(root))
    os.environ["HERMES_HOME"] = str(hermes_home)
    os.environ["HERMES_ANDROID_EMBEDDED"] = "1"
    os.environ.setdefault("HERMES_DESKTOP", "1")
    os.environ.setdefault("HERMES_NO_BROWSER_OPEN", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    _prepare_node_environment(root)
    os.chdir(workspace)
    _files_dir = str(root)
    return {
        "files_dir": str(root),
        "hermes_home": str(hermes_home),
        "workspace": str(workspace),
        "logs": str(logs),
    }


def _prepend_env_path(name: str, value: Path) -> None:
    current = os.environ.get(name, "")
    parts = [part for part in current.split(os.pathsep) if part]
    value_text = str(value)
    if value_text not in parts:
        parts.insert(0, value_text)
    os.environ[name] = os.pathsep.join(parts)


def _prepare_node_environment(root: Path) -> None:
    runtime = root / "hermes-node"
    tui_runtime = root / "hermes-tui"
    env_node = os.environ.get("HERMES_NODE", "").strip()
    node = Path(env_node) if env_node else runtime / "bin" / "node"
    lib = runtime / "lib"
    if not node.is_file():
        return

    os.environ["HERMES_NODE"] = str(node)
    if (tui_runtime / "dist" / "entry.js").is_file():
        os.environ["HERMES_TUI_DIR"] = str(tui_runtime)
    os.environ["HERMES_SKIP_NODE_BOOTSTRAP"] = "1"
    os.environ.setdefault("NODE_ENV", "production")
    os.environ.setdefault("TERM", "xterm-256color")
    _prepend_env_path("PATH", runtime / "bin")
    if lib.is_dir():
        _prepend_env_path("LD_LIBRARY_PATH", lib)


def initialize(files_dir: str, port: int = 9129) -> str:
    """Prepare local directories and verify the embedded source imports."""
    global _server_port, _last_error
    with _lock:
        _server_port = int(port or _server_port)
        env = _prepare_environment(files_dir)
        try:
            import hermes_cli  # noqa: F401
            import run_agent  # noqa: F401
            import gateway  # noqa: F401
            _last_error = ""
            return _json({
                "ok": True,
                "available": True,
                "port": _server_port,
                "running": is_running(),
                "env": env,
            })
        except Exception as exc:
            _last_error = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            return _json({
                "ok": False,
                "available": False,
                "port": _server_port,
                "running": False,
                "env": env,
                "error": _last_error,
            })


def _run_server(host: str, port: int) -> None:
    global _last_error
    try:
        from hermes_cli.web_server import start_server

        start_server(
            host=host,
            port=port,
            open_browser=False,
            allow_public=False,
            initial_profile="",
        )
    except BaseException as exc:
        _last_error = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-8000:]


def start(files_dir: str, port: int = 9129) -> str:
    """Start Hermes backend on localhost inside the app process."""
    global _server_thread, _server_port, _started_at, _last_error
    with _lock:
        _server_port = int(port or _server_port)
        env_status = json.loads(initialize(files_dir, _server_port))
        if not env_status.get("ok"):
            return _json(env_status)

        if is_running():
            return status()

        _last_error = ""
        _started_at = time.time()
        _server_thread = threading.Thread(
            target=_run_server,
            args=("127.0.0.1", _server_port),
            name="hermes-android-backend",
            daemon=True,
        )
        _server_thread.start()

    deadline = time.time() + 20
    while time.time() < deadline:
        if is_running():
            return status()
        if _last_error:
            return status()
        time.sleep(0.25)
    return status()


def is_running() -> bool:
    return _is_port_open("127.0.0.1", _server_port)


def status() -> str:
    with _lock:
        uptime = max(0.0, time.time() - _started_at) if _started_at else 0.0
        running = is_running()
        body: dict[str, Any] | None = None
        if running:
            try:
                with urlopen(f"http://127.0.0.1:{_server_port}/api/status", timeout=1.5) as response:
                    raw = response.read().decode("utf-8", errors="replace")
                    body = json.loads(raw)
            except Exception:
                body = None
        return _json({
            "ok": running and not _last_error,
            "available": True,
            "running": running,
            "port": _server_port,
            "url": f"http://127.0.0.1:{_server_port}",
            "uptime_seconds": round(uptime, 3),
            "thread_alive": bool(_server_thread and _server_thread.is_alive()),
            "files_dir": _files_dir,
            "error": _last_error,
            "api_status": body,
        })


def diagnose(files_dir: str, port: int = 9129) -> str:
    init = json.loads(initialize(files_dir, port))
    stat = json.loads(status())
    return _json({
        "ok": bool(init.get("ok")),
        "init": init,
        "status": stat,
    })


def run_command(command_json: str, files_dir: str, port: int = 9129) -> str:
    try:
        request = json.loads(command_json or "{}")
    except Exception:
        request = {}
    command = str(request.get("command") or "status").strip().lower()
    if command in {"start", "run", "serve"}:
        return start(files_dir, port)
    if command in {"diagnose", "doctor"}:
        return diagnose(files_dir, port)
    if command in {"status", "version"}:
        return status()
    return _json({
        "ok": False,
        "available": True,
        "running": is_running(),
        "port": port,
        "error": f"Unsupported embedded command: {command}",
    })
