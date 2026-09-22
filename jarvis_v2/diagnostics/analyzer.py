"""Bounded parsing of logs, stack traces and test output."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import re

@dataclass(frozen=True)
class DiagnosticEvent:
    kind: str
    message: str
    source: str = ""
    line: int = 0
    severity: str = "error"
    context: dict | None = None

class DiagnosticAnalyzer:
    def analyze_text(self, text: str, source: str = "runtime") -> list[DiagnosticEvent]:
        if len(text) > 2_000_000: raise ValueError("Diagnostic input exceeds limit")
        events=[]
        lines=text.splitlines()
        for i,line in enumerate(lines,1):
            if re.search(r"Traceback \(most recent call last\)",line):
                events.append(DiagnosticEvent("exception","Python traceback",source,i,"error"))
            m=re.search(r"File [\"'](.+?)[\"'], line (\d+)",line)
            if m:
                events.append(DiagnosticEvent("stack_frame",line.strip(),m.group(1),int(m.group(2)),"error"))
            if re.search(r"\b(ERROR|CRITICAL|FATAL)\b",line,re.I):
                events.append(DiagnosticEvent("log_error",line.strip(),source,i,"error"))
            elif re.search(r"\b(WARN|WARNING)\b",line,re.I):
                events.append(DiagnosticEvent("log_warning",line.strip(),source,i,"warning"))
            if re.search(r"FAILED|ERROR.*test",line):
                events.append(DiagnosticEvent("test_failure",line.strip(),source,i,"error"))
        return events

    def analyze_file(self, path: str | Path) -> list[DiagnosticEvent]:
        p=Path(path).resolve()
        if not p.is_file(): raise FileNotFoundError(str(p))
        return self.analyze_text(p.read_text(encoding="utf-8",errors="replace"),str(p))

    def summarize(self, events: list[DiagnosticEvent]) -> dict:
        return {"total":len(events),"errors":sum(e.severity=="error" for e in events),"warnings":sum(e.severity=="warning" for e in events),"kinds":sorted({e.kind for e in events})}
