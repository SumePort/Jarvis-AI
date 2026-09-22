"""Semantic Windows UI actions with element targeting.

The model identifies an element by stable UI attributes; the adapter resolves
that target locally and performs the requested action only after authorization.
"""
from __future__ import annotations
from typing import Any
from jarvis_v2.core.types import ToolSpec, ActionRisk, DataClass

class SemanticUIActions:
    def _desktop(self):
        from pywinauto import Desktop
        return Desktop(backend="uia")

    def _find(self, name: str | None=None, control_type: str | None=None,
              automation_id: str | None=None, title: str | None=None):
        desktop=self._desktop()
        windows=desktop.windows(title=title) if title else desktop.windows()
        for window in windows:
            try:
                matches=window.descendants(control_type=control_type) if control_type else window.descendants()
            except Exception:
                continue
            for element in matches:
                try:
                    info=element.element_info
                    if automation_id and (info.automation_id or "") != automation_id: continue
                    if name and (element.window_text() or "") != name: continue
                    return element
                except Exception:
                    continue
        raise LookupError("UI element not found")

    def click(self, name: str | None=None, control_type: str | None=None,
              automation_id: str | None=None, window_title: str | None=None):
        element=self._find(name, control_type, automation_id, window_title)
        element.click_input()
        return {"clicked": name or automation_id or control_type}

    def type_text(self, text: str, name: str | None=None, control_type: str="Edit",
                  automation_id: str | None=None, window_title: str | None=None):
        element=self._find(name, control_type, automation_id, window_title)
        element.set_edit_text(text)
        return {"typed_chars": len(text), "target": name or automation_id or control_type}

    def select(self, name: str, control_type: str="ListItem", window_title: str | None=None):
        element=self._find(name, control_type, None, window_title)
        element.select()
        return {"selected": name}

def semantic_ui_specs() -> list[ToolSpec]:
    return [
        ToolSpec("ui_click","Click a named Windows UI element",{"name":"string","control_type":"string","automation_id":"string","window_title":"string"},("os.windows","pywinauto"),ActionRisk.CONFIRM,DataClass.CONTROLLED),
        ToolSpec("ui_type_text","Type into a named Windows text control",{"text":"string","name":"string","control_type":"string","automation_id":"string","window_title":"string"},("os.windows","pywinauto"),ActionRisk.CONFIRM,DataClass.CONTROLLED),
        ToolSpec("ui_select","Select a named Windows list item",{"name":"string","control_type":"string","window_title":"string"},("os.windows","pywinauto"),ActionRisk.CONFIRM,DataClass.CONTROLLED),
    ]
