from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import os
import re
import subprocess
import sys
from typing import Iterable


@dataclass
class TestFailure:
    framework: str
    test_name: str
    message: str
    file: str | None = None
    line: int | None = None
    raw: str = ""

    def to_dict(self) -> dict:
        return {
            "framework": self.framework,
            "test_name": self.test_name,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "raw": self.raw,
        }


@dataclass
class TestRunResult:
    framework: str
    command: list[str]
    return_code: int
    passed: bool
    failures: list[TestFailure] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict:
        return {
            "framework": self.framework,
            "command": self.command,
            "return_code": self.return_code,
            "passed": self.passed,
            "failures": [f.to_dict() for f in self.failures],
        }


@dataclass
class TestSuite:
    framework: str
    command: list[str]
    test_files: list[str]
    config_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "framework": self.framework,
            "command": self.command,
            "test_files": self.test_files,
            "config_files": self.config_files,
        }


class TestIntelligence:
    """Discover and run bounded project tests without exposing arbitrary shell execution."""

    IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist"}

    def __init__(self, root: str | Path, timeout_seconds: int = 120, max_output: int = 200_000):
        self.root = Path(root).resolve()
        self.timeout_seconds = timeout_seconds
        self.max_output = max_output

    def _files(self) -> Iterable[Path]:
        if not self.root.exists():
            return []
        for base, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS]
            for name in files:
                yield Path(base) / name

    def discover(self) -> list[TestSuite]:
        suites: list[TestSuite] = []
        files = list(self._files())

        py_tests = [str(p.relative_to(self.root)) for p in files
                    if p.suffix == ".py" and (p.name.startswith("test_") or p.name.endswith("_test.py"))]
        if py_tests:
            if any(p.name == "pytest.ini" for p in files):
                config = ["pytest.ini"]
            elif any(p.name == "pyproject.toml" for p in files):
                config = ["pyproject.toml"]
            else:
                config = []
            suites.append(TestSuite("pytest", [sys.executable, "-m", "pytest", "-q"], sorted(py_tests), config))

        package = self.root / "package.json"
        js_tests = [str(p.relative_to(self.root)) for p in files
                    if p.suffix in {".js", ".jsx", ".ts", ".tsx"} and
                    (".test." in p.name or ".spec." in p.name)]
        if package.exists() and js_tests:
            try:
                data = json.loads(package.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}
            script = data.get("scripts", {}).get("test")
            if script:
                suites.append(TestSuite("npm", ["npm", "test", "--", "--runInBand"], sorted(js_tests), ["package.json"]))

        dart_tests = [str(p.relative_to(self.root)) for p in files
                      if p.suffix == ".dart" and p.parts[-2:] and "test" in p.parts]
        if (self.root / "pubspec.yaml").exists() and dart_tests:
            suites.append(TestSuite("flutter", ["flutter", "test"], sorted(dart_tests), ["pubspec.yaml"]))

        return suites

    def run(self, suite: TestSuite) -> TestRunResult:
        if suite.framework not in {"pytest", "npm", "flutter"}:
            raise ValueError(f"Unsupported test framework: {suite.framework}")
        try:
            proc = subprocess.run(
                suite.command,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                shell=False,
            )
            stdout = proc.stdout[-self.max_output:]
            stderr = proc.stderr[-self.max_output:]
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "")[-self.max_output:]
            stderr = (exc.stderr or "")[-self.max_output:]
            failure = TestFailure(suite.framework, "<timeout>",
                                  f"Test command timed out after {self.timeout_seconds}s",
                                  raw=f"{stdout}\n{stderr}")
            return TestRunResult(suite.framework, suite.command, -1, False, [failure], stdout, stderr)

        failures = self.parse_failures(suite.framework, stdout + "\n" + stderr)
        return TestRunResult(suite.framework, suite.command, proc.returncode,
                             proc.returncode == 0 and not failures, failures, stdout, stderr)

    def parse_failures(self, framework: str, text: str) -> list[TestFailure]:
        if framework == "pytest":
            return self._parse_pytest(text)
        if framework == "npm":
            return self._parse_generic(text, framework)
        if framework == "flutter":
            return self._parse_generic(text, framework)
        return []

    def _parse_pytest(self, text: str) -> list[TestFailure]:
        failures: list[TestFailure] = []
        lines = text.splitlines()
        current = None
        for i, line in enumerate(lines):
            m = re.match(r"^_{3,}\s*(.+?)\s*_{3,}$", line)
            if m:
                current = m.group(1).strip()
                continue
            m = re.match(r"^E\s+(.+)$", line)
            if m and current:
                message = m.group(1).strip()
                file = None
                lineno = None
                for back in lines[max(0, i-12):i]:
                    fm = re.search(r"(?:File\s+)?([A-Za-z]:[\\/][^:]+|[^\s:]+\.py):([0-9]+)", back)
                    if fm:
                        file, lineno = fm.group(1), int(fm.group(2))
                        break
                failures.append(TestFailure("pytest", current, message, file, lineno, "\n".join(lines[max(0, i-3):i+1])))
        if failures:
            return failures
        for line in lines:
            m = re.match(r"^FAILED\s+([^\s]+)(?:::(\S+))?", line)
            if m:
                failures.append(TestFailure("pytest", m.group(2) or m.group(1), "pytest reported failure", m.group(1), raw=line))
        return failures

    def _parse_generic(self, text: str, framework: str) -> list[TestFailure]:
        failures: list[TestFailure] = []
        for line in text.splitlines():
            if re.search(r"\b(FAIL|FAILED|ERROR)\b", line, re.I):
                failures.append(TestFailure(framework, "<unknown>", line.strip(), raw=line.strip()))
        return failures[:100]

    def run_all(self) -> list[TestRunResult]:
        return [self.run(suite) for suite in self.discover()]
