from __future__ import annotations

def list_windows() -> list[str]:
    try:
        import pygetwindow as gw
        return [w.title for w in gw.getAllWindows() if w.title]
    except Exception:
        return []
