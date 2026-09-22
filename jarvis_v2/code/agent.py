"""Structured coding-agent workflow with bounded execution."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any
from jarvis_v2.code.workspace import ProjectWorkspace


@dataclass(frozen=True)
class CodeTask:
    goal: str
    project_root: str


class CodeExecutor(Protocol):
    def execute(self, command: str, project_root: str) -> object: ...


class CodingAgent:
    STAGES = ("understand", "plan", "edit", "test", "diagnose", "repair", "verify", "handoff")

    def __init__(self, executor: CodeExecutor | None = None) -> None:
        self.executor = executor

    def plan_stages(self) -> tuple[str, ...]:
        return self.STAGES

    def require_executor(self) -> CodeExecutor:
        if not self.executor:
            raise RuntimeError("No project execution provider configured")
        return self.executor

    def workspace(self, project_root: str) -> ProjectWorkspace:
        return ProjectWorkspace(project_root)

    def test(self, project_root: str, command: str = "pytest") -> dict[str, Any]:
        result = self.require_executor().execute(command, project_root)
        return {"stage": "test", "result": result}

    def verify(self, project_root: str, command: str = "python -m compileall .") -> dict[str, Any]:
        # compileall is deliberately not in the general executor allowlist yet;
        # callers should use an explicitly allowlisted verification command.
        result = self.require_executor().execute(command, project_root)
        return {"stage": "verify", "result": result}

    def diagnose(self, test_result: dict[str, Any]) -> dict[str, Any]:
        result = test_result.get("result", {})
        return {
            "stage": "diagnose",
            "failed": result.get("returncode", 1) != 0 if isinstance(result, dict) else True,
            "stderr": result.get("stderr", "") if isinstance(result, dict) else str(result),
        }
