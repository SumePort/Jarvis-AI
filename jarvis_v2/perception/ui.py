"""Convert structured UI accessibility data into perception evidence."""
from __future__ import annotations
from jarvis_v2.perception.types import Percept, PerceptionResult, InputKind

class UIPerception:
    def perceive(self, snapshot: dict) -> PerceptionResult:
        if not snapshot.get("available"):
            return PerceptionResult([], [{"source":"windows.ui","available":False,"reason":snapshot.get("reason")}])
        elements=snapshot.get("elements", [])
        text=[]
        for e in elements:
            name=e.get("name", "")
            ctype=e.get("control_type", "")
            if name or ctype: text.append(f"{ctype}: {name}".strip())
        percept=Percept(InputKind.ENVIRONMENT, "\\n".join(text), "windows.ui", 0.98, "normal", {"element_count":len(elements)})
        return PerceptionResult([percept], [{"source":"windows.ui","element_count":len(elements)}])
