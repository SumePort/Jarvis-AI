from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import ast
import difflib
import re

from jarvis_v2.tests.intelligence import TestFailure


@dataclass
class RepairCandidate:
    file: str
    start_line: int
    end_line: int
    reason: str
    confidence: float
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "reason": self.reason,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }


@dataclass
class PatchProposal:
    file: str
    original: str
    proposed: str
    unified_diff: str
    reason: str
    confidence: float
    requires_confirmation: bool = True

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "unified_diff": self.unified_diff,
            "reason": self.reason,
            "confidence": self.confidence,
            "requires_confirmation": self.requires_confirmation,
        }


class CodeRepairIntelligence:
    """Find bounded repair locations and generate reviewable patch proposals.

    This layer never writes files and never executes generated code.
    """

    def __init__(self, root: str | Path, max_file_size: int = 1_000_000):
        self.root = Path(root).resolve()
        self.max_file_size = max_file_size

    def locate(self, failure: TestFailure) -> list[RepairCandidate]:
        if not failure.file:
            return []
        path = Path(failure.file)
        if not path.is_absolute():
            path = (self.root / path).resolve()
        else:
            path = path.resolve()
        try:
            path.relative_to(self.root)
        except ValueError:
            return []
        if not path.is_file() or path.stat().st_size > self.max_file_size:
            return []

        candidates: list[RepairCandidate] = []
        if failure.line:
            candidates.append(
                RepairCandidate(
                    str(path),
                    failure.line,
                    failure.line,
                    "Test failure points to this source line.",
                    0.95,
                    [failure.test_name, failure.message],
                )
            )

        if path.suffix == ".py":
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                return candidates
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    end = getattr(node, "end_lineno", node.lineno)
                    if failure.line and node.lineno <= failure.line <= end:
                        candidates.insert(
                            0,
                            RepairCandidate(
                                str(path), node.lineno, end,
                                f"Failure line is inside {node.__class__.__name__.lower()} '{node.name}'.",
                                0.98,
                                [failure.test_name, failure.message],
                            ),
                        )
                        break
        return candidates

    def propose_text_patch(
        self,
        file: str | Path,
        new_text: str,
        reason: str,
        confidence: float = 0.5,
    ) -> PatchProposal:
        path = Path(file).resolve()
        try:
            path.relative_to(self.root)
        except ValueError:
            raise ValueError("Patch target must remain inside project root")
        if not path.is_file():
            raise FileNotFoundError(str(path))
        original = path.read_text(encoding="utf-8", errors="replace")
        if len(original) > self.max_file_size or len(new_text) > self.max_file_size:
            raise ValueError("Patch exceeds file size limit")
        diff = "".join(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile=str(path),
                tofile=str(path),
            )
        )
        if not diff:
            raise ValueError("Proposed patch makes no changes")
        return PatchProposal(str(path), original, new_text, diff, reason, max(0.0, min(1.0, confidence)))

    def suggest_assertion_repairs(self, failure: TestFailure) -> list[str]:
        """Return conservative hints; these are not automatic edits."""
        msg = failure.message.lower()
        hints = []
        if "assert" in msg:
            hints.append("Inspect the expected-vs-actual assertion and the producing function.")
        if "nameerror" in msg:
            hints.append("Check imports, spelling, and symbol scope.")
        if "typeerror" in msg:
            hints.append("Check argument count, argument types, and API contract.")
        if "attributeerror" in msg:
            hints.append("Check object type and attribute/API availability.")
        if "importerror" in msg or "modulenotfounderror" in msg:
            hints.append("Check dependency installation and import path before changing source.")
        if "syntaxerror" in msg:
            hints.append("Inspect the reported syntax location and the preceding statement.")
        return hints
