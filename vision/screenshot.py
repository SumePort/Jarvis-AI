from __future__ import annotations
from pathlib import Path

def capture(path: str="data/screenshots/current.png") -> str:
    import pyautogui
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    pyautogui.screenshot().save(p)
    return str(p.resolve())
