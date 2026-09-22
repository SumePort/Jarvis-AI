"""Research-to-code self-improvement orchestration for JARVIS."""
from __future__ import annotations
from dataclasses import dataclass
import json
from jarvis_v2.self_improvement.engine import SelfImprovementEngine, ImprovementPlan

PROTECTED_PATH_PREFIXES = (
    "jarvis_v2/security/",
    "jarvis_v2/audit/",
    "jarvis_v2/doom/vault",
    "jarvis_v2/doom/policy.py",
    "jarvis_v2/self_improvement/",
    "jarvis_v2/devices/session_manager.py",
)

@dataclass(frozen=True)
class ImprovementRequest:
    goal: str
    technology: str
    research_query: str | None = None

@dataclass
class ImprovementWorkflow:
    request: ImprovementRequest
    status: str = "created"
    plan: ImprovementPlan | None = None
    changed_files: tuple[str, ...] = ()
    tests: dict | None = None
    result: object | None = None
    message: str = ""

class SelfImprovementOrchestrator:
    """Coordinate research, model planning, isolated edits and verification.

    Ordinary self-improvement cannot edit security boundaries or promote code.
    """

    def __init__(self, engine: SelfImprovementEngine, brain=None,
                 research=None, learning_store=None):
        self.engine = engine
        self.brain = brain
        self.research = research
        self.learning_store = learning_store

    def _validate_paths(self, files: list[str]) -> None:
        root = self.engine.root
        for path in files:
            resolved = (root / path).resolve()
            if root not in resolved.parents and resolved != root:
                raise PermissionError(f"Path escapes project root: {path}")
            normalized = resolved.relative_to(root).as_posix()
            if any(normalized == p or normalized.startswith(p) for p in PROTECTED_PATH_PREFIXES):
                raise PermissionError(f"Protected self-improvement path: {normalized}")

    def _plan_from_model(self, request: ImprovementRequest, evidence: str) -> ImprovementPlan:
        if self.brain is None:
            raise RuntimeError("No model brain configured for self-improvement planning")
        prompt = (
            "Create a JSON self-improvement plan for JARVIS. "
            "Only propose files that need compatibility changes. "
            "Never propose security, authentication, vault, audit, DOOM policy, "
            "device-session, or self-improvement files. "
            "Return exactly: {goal, files, rationale, tests}. "
            f"Goal: {request.goal}\nTechnology: {request.technology}\n"
            f"Research evidence:\n{evidence[:18000]}"
        )
        raw = self.brain.respond(prompt)
        data = json.loads(raw) if isinstance(raw, str) else raw
        files = [str(x) for x in data.get("files", [])]
        tests = [str(x) for x in data.get("tests", [])]
        self._validate_paths(files)
        return self.engine.prepare(str(data.get("goal") or request.goal), files, tests)

    def prepare(self, request: ImprovementRequest) -> ImprovementWorkflow:
        workflow = ImprovementWorkflow(request, status="researching")
        evidence = ""
        if self.research is not None:
            query = request.research_query or (
                f"{request.technology} compatibility integration Python JARVIS"
            )
            evidence = self.research.search(query, limit=5).synthesis_context
        workflow.status = "planning"
        workflow.plan = self._plan_from_model(request, evidence)
        workflow.status = "planned"
        return workflow

    def apply_and_verify(self, workflow: ImprovementWorkflow,
                         edits: dict[str, str]) -> ImprovementWorkflow:
        if workflow.plan is None:
            raise RuntimeError("Improvement must be planned before edits")
        branch = self.engine.create_branch(workflow.plan)
        workflow.status = "editing"
        workflow.changed_files = self.engine.apply(workflow.plan, edits)
        workflow.status = "testing"
        workflow.tests = self.engine.test(list(workflow.plan.tests) or ["pytest"])
        workflow.result = self.engine.review(workflow.plan, workflow.changed_files, workflow.tests)
        workflow.status = "ready_for_review" if workflow.tests.get("passed") else "failed"
        workflow.message = f"Isolated on branch {branch}. Promotion requires explicit approval."
        return workflow
