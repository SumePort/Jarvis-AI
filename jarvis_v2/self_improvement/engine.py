"""Controlled self-improvement engine for JARVIS.

JARVIS may inspect its own repository, create an isolated improvement branch,
apply an explicitly scoped change, run tests, and prepare a review artifact.
Promotion to the active runtime remains a separate approval step.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import uuid
from jarvis_v2.code.workspace import ProjectWorkspace


@dataclass
class ImprovementPlan:
    goal: str
    files: tuple[str, ...] = ()
    rationale: str = ""
    tests: tuple[str, ...] = ()


@dataclass
class ImprovementResult:
    improvement_id: str
    status: str
    branch: str
    changed_files: tuple[str, ...] = ()
    test_output: dict | None = None
    message: str = ""


class SelfImprovementEngine:
    """Self-modification with isolation, tests, auditability and rollback."""

    def __init__(self, project_root: str, executor=None):
        self.root = Path(project_root).resolve()
        self.workspace = ProjectWorkspace(str(self.root))
        self.executor = executor

    def inspect(self) -> dict:
        files = []
        for path in self.root.rglob("*"):
            if path.is_file() and not any(part in ProjectWorkspace.IGNORED for part in path.relative_to(self.root).parts):
                files.append(str(path.relative_to(self.root)))
        return {"root": str(self.root), "files": files[:500]}

    def prepare(self, goal: str, files: list[str], tests: list[str]) -> ImprovementPlan:
        safe = tuple(self.workspace.resolve(f).relative_to(self.root).as_posix() for f in files)
        return ImprovementPlan(goal, safe, "Scoped self-improvement proposal", tuple(tests))

    def create_branch(self, plan: ImprovementPlan) -> str:
        branch = "jarvis/improve/" + uuid.uuid4().hex[:12]
        self._git(["checkout", "-b", branch])
        return branch

    def apply(self, plan: ImprovementPlan, edits: dict[str, str]) -> tuple[str, ...]:
        allowed = set(plan.files)
        if set(edits) - allowed:
            raise PermissionError("Improvement attempted to edit files outside its approved scope")
        changed = []
        for path, content in edits.items():
            self.workspace.write(path, content)
            changed.append(path)
        return tuple(changed)

    def test(self, commands: list[str] | None = None) -> dict:
        if self.executor is None:
            raise RuntimeError("No bounded project executor configured")
        results = []
        for command in commands or ["pytest"]:
            results.append(self.executor.execute(command, str(self.root)))
        return {"passed": all(r.get("returncode", 1) == 0 for r in results), "results": results}

    def review(self, plan: ImprovementPlan, changed: tuple[str, ...], tests: dict) -> ImprovementResult:
        return ImprovementResult(
            "improve_" + uuid.uuid4().hex[:16],
            "ready_for_review" if tests.get("passed") else "failed",
            self._current_branch(),
            changed,
            tests,
            "Promotion requires explicit approval.",
        )

    def rollback(self) -> None:
        self._git(["reset", "--hard", "HEAD"])
        self._git(["checkout", "-"])

    def _git(self, args: list[str]) -> str:
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "git command failed")
        return result.stdout.strip()

    def _current_branch(self) -> str:
        return self._git(["branch", "--show-current"])
