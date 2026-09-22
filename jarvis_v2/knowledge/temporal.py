from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import re


@dataclass
class CommitSnapshot:
    commit: str
    timestamp: str
    author: str
    subject: str
    changed_files: list[str] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class TemporalChange:
    path: str
    commits: list[str] = field(default_factory=list)
    first_seen: str | None = None
    last_changed: str | None = None
    total_additions: int = 0
    total_deletions: int = 0

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class TemporalIntelligence:
    """Read-only Git history analysis for reconstructing how a project evolved."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=self.root, capture_output=True,
            text=True, timeout=30, shell=False, check=False
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "git command failed")
        return result.stdout

    def commits(self, limit: int = 50) -> list[CommitSnapshot]:
        limit = max(1, min(limit, 500))
        fmt = "%H%x1f%aI%x1f%an%x1f%s%x1e"
        raw = self._git("log", f"-{limit}", f"--format={fmt}", "--numstat")
        result = []
        for block in raw.split("\x1e"):
            block = block.strip()
            if not block:
                continue
            lines = block.splitlines()
            header = lines[0].split("\x1f")
            if len(header) != 4:
                continue
            changed, additions, deletions = [], 0, 0
            for line in lines[1:]:
                parts = line.split("\t")
                if len(parts) == 3:
                    try:
                        additions += int(parts[0])
                        deletions += int(parts[1])
                    except ValueError:
                        continue
                    changed.append(parts[2])
            result.append(CommitSnapshot(header[0], header[1], header[2], header[3], changed, additions, deletions))
        return result

    def file_history(self, path: str, limit: int = 30) -> TemporalChange:
        safe = Path(path)
        resolved = (self.root / safe).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError:
            raise ValueError("path escapes project root")
        rel = resolved.relative_to(self.root).as_posix()
        raw = self._git("log", f"-{max(1, min(limit, 200))}", "--format=%H%x1f%aI", "--numstat", "--", rel)
        commits, dates, additions, deletions = [], [], 0, 0
        for line in raw.splitlines():
            parts = line.split("\x1f")
            if len(parts) == 2 and len(parts[0]) >= 7:
                commits.append(parts[0]); dates.append(parts[1])
            else:
                nums = line.split("\t")
                if len(nums) == 3:
                    try:
                        additions += int(nums[0]); deletions += int(nums[1])
                    except ValueError:
                        pass
        return TemporalChange(rel, commits, min(dates) if dates else None, max(dates) if dates else None, additions, deletions)

    def changes_between(self, older: str, newer: str = "HEAD") -> list[str]:
        return [line.strip() for line in self._git("diff", "--name-only", f"{older}..{newer}").splitlines() if line.strip()]

    def explain_path(self, path: str, limit: int = 10) -> list[str]:
        history = self.file_history(path, limit)
        return history.commits
