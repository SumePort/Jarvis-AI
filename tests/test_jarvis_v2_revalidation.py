from jarvis_v2.knowledge.findings import EvidenceItem, Finding
from jarvis_v2.knowledge.lifecycle import RevalidationRequest
from jarvis_v2.knowledge.revalidation import RevalidationPlanner


def test_revalidation_uses_original_evidence():
    finding = Finding(
        "fd_1", "API uses PostgreSQL", "verified", 0.8,
        ["ev_1", "ev_2"],
    )
    evidence = [
        EvidenceItem("ev_1", "config", "database config", "config", 0.9),
        EvidenceItem("ev_2", "test", "database test", "pytest", 0.9),
    ]
    request = RevalidationRequest("fd_1", "stale", 10, "revalidate_finding")

    plan = RevalidationPlanner().plan(request, finding, evidence)

    assert not plan.blocked
    assert len(plan.steps) == 2
    assert {step.action for step in plan.steps} == {"inspect_config", "run_targeted_test"}
