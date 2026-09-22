"""Bounded Windows control adapters with explicit risk contracts."""
from __future__ import annotations
import os, subprocess
from typing import Any
from jarvis_v2.core.types import ToolSpec, ActionRisk, DataClass

class WindowsAdapters:
    def type_text(self, text: str) -> dict[str, Any]:
        import pyperclip, pyautogui
        pyperclip.copy(text); pyautogui.hotkey("ctrl", "v")
        return {"typed_chars": len(text)}
    def press_key(self, key: str) -> dict[str, Any]:
        import pyautogui
        pyautogui.press(key); return {"key": key}
    def click(self, x: int, y: int, button: str="left") -> dict[str, Any]:
        import pyautogui
        pyautogui.click(x, y, button=button); return {"x":x,"y":y,"button":button}
    def scroll(self, amount: int) -> dict[str, Any]:
        import pyautogui
        pyautogui.scroll(amount); return {"amount":amount}
    def close_app(self, name: str) -> dict[str, Any]:
        if os.name != "nt": raise RuntimeError("Windows only")
        subprocess.run(["taskkill", "/IM", name, "/T"], check=False, capture_output=True, text=True)
        return {"requested_close":name}

def windows_tool_specs() -> list[ToolSpec]:
    return [
        ToolSpec("type_text","Type text into the active window",{"text":"string"},("os.windows","pyautogui"),ActionRisk.CONFIRM,DataClass.CONTROLLED),
        ToolSpec("press_key","Press a keyboard key",{"key":"string"},("os.windows","pyautogui"),ActionRisk.CONFIRM,DataClass.CONTROLLED),
        ToolSpec("click","Click screen coordinates",{"x":"integer","y":"integer","button":"string"},("os.windows","pyautogui"),ActionRisk.CONFIRM,DataClass.CONTROLLED),
        ToolSpec("scroll","Scroll the active window",{"amount":"integer"},("os.windows","pyautogui"),ActionRisk.CONFIRM,DataClass.NORMAL),
        ToolSpec("close_app","Request application termination",{"name":"string"},("os.windows",),ActionRisk.CONFIRM,DataClass.NORMAL),
    ]
