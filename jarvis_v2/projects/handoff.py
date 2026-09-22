from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import subprocess


@dataclass
class HandoffReport:
    branch: str
    changed_files: list[str] = field(default_factory=list)
    tests_passed: bool = False
    documentation_ready: bool = False
    commit_message: str = ""
    requires_confirmation: bool = True

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class ProjectHandoff:
    """Prepare a project hand-off without committing or pushing automatically."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def _git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, shell=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "git command failed")
        return result.stdout.strip()

    def prepare(self, commit_message: str, tests_passed: bool = False, documentation_ready: bool = False) -> HandoffReport:
        branch = self._git("branch", "--show-current")
        status = self._git("status", "--porcelain")
        changed = [line[3:] for line in status.splitlines() if len(line) >= 4]
        return HandoffReport(branch, changed, tests_passed, documentation_ready, commit_message)

    def commit(self, report: HandoffReport, confirmed: bool = False) -> str:
        if not confirmed:
            raise PermissionError("Explicit confirmation required before commit")
        if not report.commit_message.strip():
            raise ValueError("Commit message is required")
        if not report.tests_passed:
            raise ValueError("Project tests must pass before commit")
        self._git("add", "--", *report.changed_files)
        self._git("commit", "-m", report.commit_message)
        return self._git("rev-parse", "HEAD")

    def push(self, remote: str = "origin", branch: str | None = None, confirmed: bool = False) -> str:
        if not confirmed:
            raise PermissionError("Explicit confirmation required before push")
        target = branch or self._git("branch", "--show-current")
        self._git("push", remote, target)
        return target
