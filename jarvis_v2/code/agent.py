"""Bounded project coding-agent orchestration."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CodeTask:
    goal: str
    project_root: str


class CodeExecutor(Protocol):
    def execute(self, command: str, project_root: str) -> object: ...


class CodingAgent:
    def __init__(self, executor: CodeExecutor | None = None) -> None:
        self.executor = executor

    def plan_stages(self) -> tuple[str, ...]:
        return ("understand", "plan", "edit", "test", "diagnose", "repair", "verify", "handoff")

    def require_executor(self) -> CodeExecutor:
        if not self.executor:
            raise RuntimeError("No project execution provider configured")
        return self.executor
