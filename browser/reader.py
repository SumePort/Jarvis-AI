"""Best-effort browser text capture through the visible Chrome window clipboard."""
from __future__ import annotations
import time

def copy_visible_page_text() -> str:
    import pyautogui, pyperclip
    pyautogui.hotkey("ctrl","a")
    time.sleep(0.2)
    pyautogui.hotkey("ctrl","c")
    time.sleep(0.4)
    text=pyperclip.paste()
    return text[:30_000]
