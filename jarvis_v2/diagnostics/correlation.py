"""Correlate diagnostics with known source files and code symbols."""
from __future__ import annotations
from dataclasses import dataclass
from .analyzer import DiagnosticEvent

@dataclass(frozen=True)
class DiagnosticLink:
    event: DiagnosticEvent
    target: str
    confidence: float

class DiagnosticCorrelator:
    def correlate(self, events: list[DiagnosticEvent], known_files: set[str]) -> list[DiagnosticLink]:
        links=[]
        for event in events:
            if event.source and event.source in known_files:
                links.append(DiagnosticLink(event,event.source,1.0))
            elif event.source:
                matches=[p for p in known_files if p.endswith(event.source) or p.endswith(event.source.replace("\\","/"))]
                if len(matches)==1: links.append(DiagnosticLink(event,matches[0],0.8))
        return links
