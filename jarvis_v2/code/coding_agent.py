from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from jarvis_v2.code.repair import CodeRepairIntelligence, PatchProposal, RepairCandidate
from jarvis_v2.code.patch_runner import PatchRunner, RepairCycle
from jarvis_v2.diagnostics.incident import IncidentReport
from jarvis_v2.diagnostics.root_cause import RootCauseInvestigator, RootCauseInvestigation
from jarvis_v2.tests.intelligence import TestFailure, TestIntelligence, TestRunResult


@dataclass
class CodingAgentRequest:
    task: str
    project_root: str
    confirmed: bool = False
    max_repair_cycles: int = 2

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class CodingAgentStep:
    phase: str
    summary: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"phase": self.phase, "summary": self.summary, "details": self.details}


@dataclass
class CodingAgentResult:
    request: CodingAgentRequest
    success: bool
    steps: list[CodingAgentStep] = field(default_factory=list)
    test_runs: list[TestRunResult] = field(default_factory=list)
    candidates: list[RepairCandidate] = field(default_factory=list)
    repair_cycles: list[RepairCycle] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "request": self.request.to_dict(),
            "success": self.success,
            "steps": [s.to_dict() for s in self.steps],
            "test_runs": [r.to_dict() for r in self.test_runs],
            "candidates": [c.to_dict() for c in self.candidates],
            "repair_cycles": [c.to_dict() for c in self.repair_cycles],
            "message": self.message,
        }


class ProjectCodingAgent:
    """Bounded project coding loop: understand -> test -> diagnose -> repair -> verify.

    The agent deliberately does not invent source edits itself. A host supplies
    a patch proposer that can use an LLM or another code-generation system.
    All writes go through PatchRunner and require explicit confirmation.
    """

    def __init__(
        self,
        root: str | Path,
        patch_proposer: Callable[[CodingAgentRequest, TestFailure, list[RepairCandidate]], PatchProposal | None],
        timeout_seconds: int = 120,
    ):
        self.root = Path(root).resolve()
        self.tests = TestIntelligence(self.root, timeout_seconds=timeout_seconds)
        self.repair = CodeRepairIntelligence(self.root)
        self.patches = PatchRunner(self.root, timeout_seconds=timeout_seconds)
        self.patch_proposer = patch_proposer

    def run(self, request: CodingAgentRequest) -> CodingAgentResult:
        if Path(request.project_root).resolve() != self.root:
            raise ValueError("Request project_root must match the agent root")

        result = CodingAgentResult(request=request, success=False)
        suites = self.tests.discover()
        result.steps.append(CodingAgentStep("understand", "Discovered project test suites.", {"suites": [s.to_dict() for s in suites]}))

        if not suites:
            result.message = "No supported test suite was discovered."
            return result

        initial = self.tests.run_all()
        result.test_runs.extend(initial)
        result.steps.append(CodingAgentStep("test", "Ran the project's discovered test suites."))

        if all(run.passed for run in initial):
            result.success = True
            result.message = "Project tests already pass; no repair was required."
            result.steps.append(CodingAgentStep("verify", result.message))
            return result

        failures = [failure for run in initial for failure in run.failures]
        for cycle_index in range(max(0, min(request.max_repair_cycles, 5))):
            if not failures:
                break
            candidates: list[RepairCandidate] = []
            for failure in failures:
                candidates.extend(self.repair.locate(failure))
            result.candidates = candidates
            result.steps.append(CodingAgentStep(
                "diagnose", "Located bounded repair candidates.",
                {"failure_count": len(failures), "candidate_count": len(candidates)},
            ))

            if not request.confirmed:
                result.message = "A repair is available but requires explicit confirmation before source changes."
                result.steps.append(CodingAgentStep("plan", result.message))
                return result

            proposal = self.patch_proposer(request, failures[0], candidates)
            if proposal is None:
                result.message = "No patch proposal was produced."
                return result

            result.steps.append(CodingAgentStep("implement", "Received a reviewable patch proposal.", {"patch": proposal.to_dict()}))
            cycle = self.patches.run_and_verify(proposal, confirmed=True)
            result.repair_cycles.append(cycle)
            result.test_runs.extend(cycle.test_runs)
            if cycle.verified:
                result.success = True
                result.message = "Patch applied and verified by the project's test suites."
                result.steps.append(CodingAgentStep("verify", result.message))
                return result

            failures = [failure for run in cycle.test_runs for failure in run.failures]
            result.steps.append(CodingAgentStep("debug", "Verification failed; continuing with bounded diagnosis."))

        result.message = "Repair loop ended without verified success."
        return result
