from pathlib import Path

from jarvis_v2.diagnostics.investigator import (
    InvestigationEvidence,
    InvestigationExecutor,
    InvestigationLoop,
)
from jarvis_v2.diagnostics.root_cause import (
    CauseHypothesis,
    InvestigationAction,
    RootCauseInvestigation,
)


def test_investigation_loop_uses_registered_actions(tmp_path: Path):
    executor = InvestigationExecutor()

    def inspect(target: str) -> InvestigationEvidence:
        return InvestigationEvidence("inspect_change", target, "inspected", True)

    executor.register("inspect_change", inspect)
    investigation = RootCauseInvestigation(
        hypotheses=[CauseHypothesis("file:api.py", "api change", confidence=0.5)],
        next_actions=[InvestigationAction("inspect_change", "file:api.py", "inspect", 5)],
    )

    def reassess(hypothesis, evidence):
        return CauseHypothesis(
            hypothesis.target, hypothesis.hypothesis,
            evidence_for=["inspection succeeded"],
            confidence=0.95,
        )

    result = InvestigationLoop(executor).run(investigation, reassess)
    assert result is not None
    assert result.resolved
    assert result.evidence[0].success
