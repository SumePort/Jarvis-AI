"""Connect understanding, retrieval, planning, DOOM routing and verification."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

from jarvis_v2.actions import ActionExecutor, ActionPlan, ActionPlanner
from jarvis_v2.core.context import JarvisContext
from jarvis_v2.doom import DoomResourceRouter
from jarvis_v2.loop import AgentLoop
from jarvis_v2.memory import KnowledgeExtractor, MemoryStore
from jarvis_v2.projects.world_model import ProjectWorldModel
from jarvis_v2.reasoning import ContextRetriever, ReasoningContextBuilder

@dataclass
class RuntimeResult:
    request: str
    reasoning_context: dict[str, Any]
    plan: ActionPlan
    execution: Any = None
    learned_memory_ids: list[str] = field(default_factory=list)

class JarvisRuntime:
    """Single runtime boundary; model providers remain pluggable."""
    def __init__(self, planner: ActionPlanner, executor: ActionExecutor,
                 memory: MemoryStore | None = None, doom: DoomResourceRouter | None = None) -> None:
        self.memory=memory or MemoryStore()
        self.retriever=ContextRetriever(self.memory)
        self.context_builder=ReasoningContextBuilder(self.retriever)
        self.planner=planner
        self.executor=executor
        self.doom=doom or DoomResourceRouter()

    def build_context(self, request: str, world_model: ProjectWorldModel | None = None) -> JarvisContext:
        structured=self.context_builder.build(request, world_model)
        return JarvisContext(user_request=request, memories=structured["retrieval"]["memories"], environment=structured)

    def run(self, request: str, plan: ActionPlan, world_model: ProjectWorldModel | None = None,
            observer: Callable[[], dict[str, Any]] | None = None, confirmed: bool = False) -> RuntimeResult:
        context=self.build_context(request, world_model)
        loop=AgentLoop(self.planner, self.executor)
        execution=loop.run(plan, observer=observer, confirmed=confirmed)
        learned=[]
        if execution.verification.success and world_model:
            for record in KnowledgeExtractor().from_project(world_model.project):
                self.memory.add(record); learned.append(record.id)
        return RuntimeResult(request, context.to_model_input(), execution.plan, execution, learned)
