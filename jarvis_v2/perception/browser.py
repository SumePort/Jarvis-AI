"""Normalize browser DOM observations into JARVIS perception evidence."""
from __future__ import annotations
from jarvis_v2.perception.types import Percept, PerceptionResult, InputKind

class BrowserPerception:
    def perceive(self, snapshot: dict) -> PerceptionResult:
        elements=snapshot.get("elements", [])
        lines=[]
        for e in elements:
            label=e.get("name") or e.get("text") or e.get("value") or ""
            if label or e.get("tag"):
                lines.append(f"{e.get('tag','')}: {label}".strip())
        text="\n".join(lines)
        p=Percept(InputKind.ENVIRONMENT,text,"browser.dom",0.99,"normal",{"url":snapshot.get("url"),"title":snapshot.get("title"),"element_count":len(elements)})
        return PerceptionResult([p],[{"source":"browser.dom","url":snapshot.get("url"),"element_count":len(elements)}])
