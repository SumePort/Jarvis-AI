"""Keyboard/mouse primitives. Keep these behind the central executor."""
from __future__ import annotations

def type_text(text: str) -> str:
    import pyautogui
    pyautogui.write(text, interval=0.01)
    return "Text typed."

def press_key(key: str) -> str:
    import pyautogui
    pyautogui.press(key)
    return f"Pressed {key}."
