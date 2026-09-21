from __future__ import annotations

def hotkey(*keys: str) -> str:
    import pyautogui
    pyautogui.hotkey(*keys)
    return "Browser hotkey executed."
