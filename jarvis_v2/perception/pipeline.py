"""Fuse multimodal inputs without making vision the canonical environment model."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from .types import InputKind, Percept, PerceptionResult

class PerceptionPipeline:
    def text(self, value: str) -> PerceptionResult:
        return PerceptionResult([Percept(InputKind.TEXT, text=value, source="user")])

    def environment(self, snapshot: Any) -> PerceptionResult:
        return PerceptionResult([Percept(InputKind.ENVIRONMENT, source="environment", metadata={"snapshot": snapshot})])

    def document(self, path: str, max_chars: int = 20000) -> PerceptionResult:
        p=Path(path).expanduser().resolve()
        if not p.is_file(): raise FileNotFoundError(str(p))
        if p.stat().st_size > max_chars * 8: raise ValueError("Document exceeds bounded perception size")
        text=p.read_text(encoding="utf-8", errors="replace")
        return PerceptionResult([Percept(InputKind.DOCUMENT, text=text[:max_chars], source=str(p))])

    def image(self, path: str) -> PerceptionResult:
        p=Path(path).expanduser().resolve()
        if not p.is_file(): raise FileNotFoundError(str(p))
        return PerceptionResult([Percept(InputKind.IMAGE, source=str(p), metadata={"path":str(p)})])

    def audio(self, source: str) -> PerceptionResult:
        return PerceptionResult([Percept(InputKind.AUDIO, source=source)])

    def video(self, source: str) -> PerceptionResult:
        return PerceptionResult([Percept(InputKind.VIDEO, source=source)])

    def fuse(self, *results: PerceptionResult) -> PerceptionResult:
        percepts=[]; evidence=[]
        for result in results:
            percepts.extend(result.percepts); evidence.extend(result.evidence)
        return PerceptionResult(percepts, evidence)
