"""Minimal JARVIS V2 agent loop contract.

This first implementation is intentionally model-agnostic. A brain adapter can
later produce a Plan, while execution remains outside the language model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .context import JarvisContext
from .types import Observation, Plan


class Brain(Protocol):
    def plan(self, context: JarvisContext) -> Plan: ...
    def respond(self, context: JarvisContext, observations: list[Observation]) -> str: ...


class Executor(Protocol):
    def execute(self, context: JarvisContext, plan: Plan) -> list[Observation]: ...


@dataclass
class AgentResult:
    plan: Plan
    observations: list[Observation]
    response: str


class JarvisAgent:
    """Orchestrate perception, planning, execution and response."""

    def __init__(self, brain: Brain, executor: Executor) -> None:
        self.brain = brain
        self.executor = executor

    def run(self, context: JarvisContext) -> AgentResult:
        plan = self.brain.plan(context)
        observations = self.executor.execute(context, plan)
        response = self.brain.respond(context, observations)
        return AgentResult(plan, observations, response)
