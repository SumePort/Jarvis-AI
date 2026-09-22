from __future__ import annotations

from pathlib import Path
import re
from jarvis_v2.diagnostics.correlation import DiagnosticCorrelator, DiagnosticLink
from jarvis_v2.diagnostics.analyzer import DiagnosticEvent
from jarvis_v2.tests.intelligence import TestFailure


class TestFailureMapper:
    """Map test failures onto repository source files and diagnostic evidence."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def map_failure(self, failure: TestFailure) -> DiagnosticLink | None:
        if not failure.file:
            return None
        candidate = Path(failure.file)
        if not candidate.is_absolute():
            candidate = (self.root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            return None
        event = DiagnosticEvent(
            kind="test_failure",
            message=failure.message,
            source=str(candidate),
            line=failure.line,
            severity="error",
            context={"test_name": failure.test_name, "framework": failure.framework},
        )
        return DiagnosticCorrelator(self.root).correlate([event], [str(candidate)])[0] if candidate.exists() else None

    def map_all(self, failures: list[TestFailure]) -> list[DiagnosticLink]:
        return [link for f in failures if (link := self.map_failure(f)) is not None]
