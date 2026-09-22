"""Structured Windows UI accessibility snapshot adapter.

Uses pywinauto when available. It is read-only: no UI action is performed here.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import importlib.util

@dataclass(frozen=True)
class UIElement:
    name: str
    control_type: str
    automation_id: str = ""
    class_name: str = ""
    enabled: bool = True
    visible: bool = True
    bounds: dict[str, int] | None = None
    value: str | None = None

class WindowsUIProvider:
    def available(self) -> bool:
        return importlib.util.find_spec("pywinauto") is not None

    def snapshot(self, title: str | None = None, max_depth: int = 4, max_elements: int = 250) -> dict[str, Any]:
        if not self.available():
            return {"available": False, "reason": "pywinauto is not installed", "elements": []}
        if max_depth < 0 or max_elements <= 0:
            raise ValueError("Invalid UI snapshot bounds")
        from pywinauto import Desktop
        windows = Desktop(backend="uia").windows(title=title) if title else Desktop(backend="uia").windows()
        elements: list[UIElement] = []
        for window in windows:
            if len(elements) >= max_elements: break
            try:
                self._walk(window, 0, max_depth, elements, max_elements)
            except Exception:
                continue
        return {"available": True, "title_filter": title, "elements": [asdict(x) for x in elements]}

    def _walk(self, control, depth, max_depth, out, limit):
        if len(out) >= limit or depth > max_depth: return
        try:
            rect=control.rectangle()
            bounds={"left":rect.left,"top":rect.top,"right":rect.right,"bottom":rect.bottom}
        except Exception:
            bounds=None
        try: name=control.window_text() or ""
        except Exception: name=""
        try: ctype=control.element_info.control_type or ""
        except Exception: ctype=""
        try: aid=control.element_info.automation_id or ""
        except Exception: aid=""
        try: cls=control.element_info.class_name or ""
        except Exception: cls=""
        try: enabled=bool(control.is_enabled())
        except Exception: enabled=True
        try: visible=bool(control.is_visible())
        except Exception: visible=True
        out.append(UIElement(name, ctype, aid, cls, enabled, visible, bounds))
        if depth == max_depth: return
        try: children=control.children()
        except Exception: children=[]
        for child in children:
            self._walk(child, depth+1, max_depth, out, limit)
