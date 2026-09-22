from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import os
import shutil
import tempfile
from typing import Callable

from jarvis_v2.code.repair import PatchProposal
from jarvis_v2.tests.intelligence import TestIntelligence, TestRunResult


@dataclass
class PatchApplication:
    applied: bool
    file: str
    before_sha256: str
    after_sha256: str | None = None
    backup: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class RepairCycle:
    proposal: PatchProposal
    application: PatchApplication
    test_runs: list[TestRunResult] = field(default_factory=list)
    verified: bool = False
    rolled_back: bool = False
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "proposal": self.proposal.to_dict(),
            "application": self.application.to_dict(),
            "test_runs": [r.to_dict() for r in self.test_runs],
            "verified": self.verified,
            "rolled_back": self.rolled_back,
            "message": self.message,
        }


class PatchRunner:
    """Apply one reviewed patch, run bounded tests, and rollback on failed verification."""

    def __init__(self, root: str | Path, timeout_seconds: int = 120):
        self.root = Path(root).resolve()
        self.tests = TestIntelligence(self.root, timeout_seconds=timeout_seconds)

    def _safe_path(self, file: str | Path) -> Path:
        path = Path(file).resolve()
        try:
            path.relative_to(self.root)
        except ValueError:
            raise ValueError("Patch target must remain inside project root")
        return path

    def apply(self, proposal: PatchProposal, confirmed: bool = False) -> PatchApplication:
        path = self._safe_path(proposal.file)
        if not confirmed:
            return PatchApplication(False, str(path), "", error="Explicit confirmation required")
        if not path.is_file():
            return PatchApplication(False, str(path), "", error="Patch target does not exist")
        current = path.read_text(encoding="utf-8", errors="replace")
        before = hashlib.sha256(current.encode("utf-8")).hexdigest()
        if current != proposal.original:
            return PatchApplication(False, str(path), before, error="File changed since patch proposal")
        fd, backup_name = tempfile.mkstemp(prefix=".jarvis-backup-", suffix=".tmp", dir=str(path.parent))
        os.close(fd)
        backup = Path(backup_name)
        shutil.copy2(path, backup)
        try:
            path.write_text(proposal.proposed, encoding="utf-8")
            after = hashlib.sha256(proposal.proposed.encode("utf-8")).hexdigest()
            return PatchApplication(True, str(path), before, after, str(backup))
        except Exception as exc:
            try:
                shutil.copy2(backup, path)
            except Exception:
                pass
            return PatchApplication(False, str(path), before, backup=str(backup), error=str(exc))

    def rollback(self, application: PatchApplication) -> bool:
        if not application.applied or not application.backup:
            return False
        path = self._safe_path(application.file)
        backup = Path(application.backup).resolve()
        if not backup.is_file():
            return False
        shutil.copy2(backup, path)
        return True

    def run_and_verify(self, proposal: PatchProposal, confirmed: bool = False) -> RepairCycle:
        application = self.apply(proposal, confirmed=confirmed)
        cycle = RepairCycle(proposal, application)
        if not application.applied:
            cycle.message = application.error or "Patch was not applied"
            return cycle
        try:
            cycle.test_runs = self.tests.run_all()
            cycle.verified = bool(cycle.test_runs) and all(r.passed for r in cycle.test_runs)
            cycle.message = "Patch verified by all discovered test suites." if cycle.verified else "Verification failed."
            if not cycle.verified:
                cycle.rolled_back = self.rollback(application)
                if cycle.rolled_back:
                    cycle.message += " Patch rolled back."
        finally:
            if application.backup:
                try:
                    Path(application.backup).unlink(missing_ok=True)
                except OSError:
                    pass
        return cycle
