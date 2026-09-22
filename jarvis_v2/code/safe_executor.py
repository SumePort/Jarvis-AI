"""Safe project execution provider for the JARVIS coding agent."""
from __future__ import annotations
from pathlib import Path
import subprocess


class SafeProjectExecutor:
    """Run only explicitly allowlisted development commands inside a project."""

    ALLOWED = (
        "python ", "python3 ", "pytest", "python -m compileall", "pyright", "ruff ",
        "git status", "git diff", "git log", "git branch",
        "flutter test", "flutter analyze", "dart test", "dart analyze",
        "npm test", "npm run test", "npm run lint",
    )

    def __init__(self, timeout: int = 120) -> None:
        self.timeout = max(5, timeout)

    def execute(self, command: str, project_root: str) -> dict:
        root = Path(project_root).resolve()
        if not root.is_dir():
            raise ValueError("Project root does not exist")
        normalized = command.strip().lower()
        if not any(normalized == allowed.strip() or normalized.startswith(allowed)
                   for allowed in self.ALLOWED):
            raise PermissionError("Command is outside the JARVIS project execution allowlist")
        completed = subprocess.run(
            command,
            cwd=str(root),
            shell=True,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout[-12000:],
            "stderr": completed.stderr[-12000:],
        }
