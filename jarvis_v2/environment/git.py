"""Git repository perception for JARVIS V2."""
from __future__ import annotations

import subprocess
from pathlib import Path
import time

from jarvis_v2.core.types import EnvironmentSnapshot


class GitEnvironmentProvider:
    def __init__(self, roots: list[str | Path] | None = None) -> None:
        self.roots = [Path(r).expanduser().resolve() for r in (roots or [Path.cwd()])]

    def snapshot(self) -> EnvironmentSnapshot:
        snapshot = EnvironmentSnapshot(timestamp=time.time())
        for root in self.roots:
            repo = self._repo_root(root)
            if repo:
                snapshot.repositories.append(self._describe(repo))
        return snapshot

    @staticmethod
    def _run(repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.stdout.strip()

    def _repo_root(self, path: Path) -> Path | None:
        if not path.is_dir():
            return None
        value = self._run(path, "rev-parse", "--show-toplevel")
        if not value:
            return None
        repo = Path(value).resolve()
        return repo if repo == path.resolve() else None

    def _describe(self, repo: Path) -> dict:
        status = self._run(repo, "status", "--short")
        branch = self._run(repo, "branch", "--show-current")
        commit = self._run(repo, "rev-parse", "HEAD")
        return {
            "root": str(repo),
            "branch": branch,
            "commit": commit,
            "dirty": bool(status),
            "changed_files": [line[3:] for line in status.splitlines() if len(line) >= 3],
        }
