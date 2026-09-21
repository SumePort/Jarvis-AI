"""Windows application launcher without arbitrary shell execution."""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

APP_ALIASES = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "control panel": "control.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
}

WINDOWS_APP_PATHS = {
    "chrome.exe": [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ],
}

def _resolve(command: str) -> str | None:
    value = APP_ALIASES.get(command.strip().lower(), command.strip())

    if os.path.isabs(value) and os.path.isfile(value):
        return value

    found = shutil.which(value)
    if found:
        return found

    for candidate in WINDOWS_APP_PATHS.get(os.path.basename(value).lower(), []):
        if candidate and Path(candidate).is_file():
            return candidate

    return None

def open_app(name: str) -> str:
    target = _resolve(name)
    if not target:
        return f"App not found: {name}"

    try:
        subprocess.Popen([target], shell=False)
        time.sleep(0.5)
        return f"Opened {name}."
    except OSError as exc:
        return f"Could not open {name}: {exc}"

def close_window(title: str) -> str:
    try:
        import win32gui, win32con
    except ImportError:
        return "pywin32 is required for window closing."

    closed = 0
    needle = title.lower()

    def handler(hwnd, _):
        nonlocal closed
        if win32gui.IsWindowVisible(hwnd) and needle in win32gui.GetWindowText(hwnd).lower():
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            closed += 1

    win32gui.EnumWindows(handler, None)
    return f"Closed {closed} matching window(s)."
