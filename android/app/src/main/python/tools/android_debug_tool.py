"""Wireless ADB control for the Hermes Android build."""

import json
import os
import subprocess
from typing import Any

from tools.registry import registry, tool_error


def _adb_path() -> str:
    native_dir = os.environ.get("HERMES_ANDROID_NATIVE_LIB_DIR", "").strip()
    return os.path.join(native_dir, "libadb_exec.so") if native_dir else ""


def _adb_home() -> str:
    return os.environ.get("HERMES_ANDROID_ADB_HOME", "").strip() or os.environ.get("HOME", "")

def check_android_debug_requirements() -> bool:
    # Android packaging guarantees the native directory is configured before Agent startup.
    return bool(os.environ.get("HERMES_ANDROID_NATIVE_LIB_DIR"))


def _run_adb(args: list[str], *, input_text: str | None = None, timeout: int = 30) -> str:
    path = _adb_path()
    if not path:
        return tool_error("Android ADB is unavailable in this Hermes runtime.")
    try:
        completed = subprocess.run(
            [path, *args],
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=_adb_home() or None,
            env={
                **os.environ,
                "HOME": _adb_home() or "/data/data/com.sesaloy.hermes/files",
                "TMPDIR": os.environ.get("TMPDIR", "/data/data/com.sesaloy.hermes/cache"),
            },
        )
        output = (completed.stdout or "") + (completed.stderr or "")
        return json.dumps(
            {
                "ok": completed.returncode == 0,
                "exit_code": completed.returncode,
                "output": output[-30000:],
            },
            ensure_ascii=False,
        )
    except subprocess.TimeoutExpired:
        return tool_error("ADB command timed out.")
    except Exception as exc:
        return tool_error(f"ADB command failed: {type(exc).__name__}: {exc}")


def android_debug_tool(
    action: str,
    host: str = "",
    port: int | None = None,
    pairing_code: str = "",
    serial: str = "",
    command: str = "",
) -> str:
    action = (action or "devices").strip().lower()
    if action == "devices":
        return _run_adb(["devices", "-l"])
    if action == "pair":
        if not host or not port or not pairing_code:
            return tool_error("pair requires host, port, and pairing_code")
        return _run_adb(["pair", f"{host}:{int(port)}"], input_text=f"{pairing_code.strip()}\n", timeout=25)
    if action == "connect":
        if not host or not port:
            return tool_error("connect requires host and port")
        return _run_adb(["connect", f"{host}:{int(port)}"], timeout=15)
    if action == "shell":
        if not command.strip():
            return tool_error("shell requires command")
        args = []
        if serial.strip():
            args = ["-s", serial.strip()]
        return _run_adb([*args, "shell", command], timeout=60)
    return tool_error("Unsupported action. Use devices, pair, connect, or shell.")


ANDROID_DEBUG_SCHEMA = {
    "name": "android_debug",
    "description": (
        "Control the paired Android phone through the APK built-in Wireless ADB. Never use terminal to look for adb; use this tool for phone operations. Use devices to inspect "
        "connections, pair/connect only with user-provided settings values, and shell "
        "for device diagnostics, screenshots, input, app launching, and file operations. "
        "Ask for confirmation before destructive commands such as deleting data, uninstalling "
        "apps, changing security settings, or factory-reset-like actions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["devices", "pair", "connect", "shell"]},
            "host": {"type": "string", "description": "Phone IP address or host."},
            "port": {"type": "integer", "description": "Wireless debugging pairing or connection port."},
            "pairing_code": {"type": "string", "description": "Six-digit pairing code shown by Android Wireless Debugging."},
            "serial": {"type": "string", "description": "ADB device serial, when more than one device is connected."},
            "command": {"type": "string", "description": "Command to execute through adb shell."},
        },
        "required": ["action"],
    },
}


registry.register(
    name="android_debug",
    toolset="terminal",
    schema=ANDROID_DEBUG_SCHEMA,
    handler=lambda args, **_: android_debug_tool(
        action=args.get("action", "devices"),
        host=args.get("host", ""),
        port=args.get("port"),
        pairing_code=args.get("pairing_code", ""),
        serial=args.get("serial", ""),
        command=args.get("command", ""),
    ),
    check_fn=check_android_debug_requirements,
    emoji="📱",
)
