from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import re


@dataclass
class ChangedFile:
    path: str
    status: str
    additions: int = 0
    deletions: int = 0
    impacted_symbols: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class ChangeImpact:
    changed_files: list[ChangedFile] = field(default_factory=list)
    affected_tests: list[str] = field(default_factory=list)
    affected_routes: list[str] = field(default_factory=list)
    affected_tables: list[str] = field(default_factory=list)
    risk: str = "low"
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "changed_files": [f.to_dict() for f in self.changed_files],
            "affected_tests": self.affected_tests,
            "affected_routes": self.affected_routes,
            "affected_tables": self.affected_tables,
            "risk": self.risk,
            "summary": self.summary,
        }


class RepositoryChangeIntelligence:
    """Read-only Git change and impact analysis."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=self.root, capture_output=True, text=True,
            timeout=20, shell=False, check=False
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "git command failed")
        return result.stdout

    def status(self) -> list[ChangedFile]:
        result = []
        for line in self._git("status", "--short").splitlines():
            if len(line) >= 4:
                result.append(ChangedFile(line[3:].strip().strip('"'), line[:2].strip() or "?"))
        return result

    def diff(self, staged: bool = False) -> str:
        return self._git("diff", "--cached", "--no-ext-diff") if staged else self._git("diff", "--no-ext-diff")

    def changed_files_between(self, base: str, head: str = "HEAD") -> list[ChangedFile]:
        names = self._git("diff", "--name-status", f"{base}...{head}").splitlines()
        nums = self._git("diff", "--numstat", f"{base}...{head}").splitlines()
        result = []
        for i, line in enumerate(names):
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            item = ChangedFile(parts[-1], parts[0])
            if i < len(nums):
                n = nums[i].split("\t")
                try:
                    item.additions, item.deletions = int(n[0]), int(n[1])
                except (ValueError, IndexError):
                    pass
            result.append(item)
        return result

    def impact(self, changed: list[ChangedFile]) -> ChangeImpact:
        tests, routes, tables = [], [], []
        for item in changed:
            p = Path(item.path)
            if p.name.startswith("test_") or ".test." in p.name or ".spec." in p.name:
                tests.append(item.path)
            if p.suffix in {".py", ".ts", ".tsx", ".js", ".jsx"}:
                routes.extend(self._find_routes(self._read(p)))
            if p.suffix == ".sql" or "migration" in p.name.lower():
                tables.extend(self._find_tables(self._read(p)))
        risk = "high" if len(changed) >= 10 or tables else "medium" if any(x.status.startswith(("A","D","R")) for x in changed) else "low"
        return ChangeImpact(
            changed, sorted(set(tests)), sorted(set(routes)), sorted(set(tables)), risk,
            f"{len(changed)} changed file(s); {len(tests)} test file(s), {len(routes)} API route(s), {len(tables)} table reference(s) affected."
        )

    def _read(self, path: Path) -> str:
        p = (self.root / path).resolve()
        try: p.relative_to(self.root)
        except ValueError: return ""
        if not p.is_file() or p.stat().st_size > 1_000_000: return ""
        return p.read_text(encoding="utf-8", errors="replace")

    @staticmethod
    def _find_routes(text: str) -> list[str]:
        return [f"{m.group(1).upper()} {m.group(2)}" for m in re.finditer(
            r'@(?:app|router)\.(get|post|put|patch|delete)\(\s*["\']([^"\']+)',
            text, re.I)]

    @staticmethod
    def _find_tables(text: str) -> list[str]:
        return re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.-]+)", text, re.I)
