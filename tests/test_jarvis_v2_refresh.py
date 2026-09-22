from jarvis_v2.knowledge.findings import EvidenceItem, Finding
from jarvis_v2.knowledge.revalidation import RevalidationPlan, RevalidationStep
from jarvis_v2.knowledge.refresh import KnowledgeRefresher, RevalidationExecutor


def test_refresh_revalidates_supported_finding():
    finding = Finding("fd_1", "API uses PostgreSQL", "stale", 0.3)
    plan = RevalidationPlan(
        "fd_1",
        [RevalidationStep("inspect_config", "config", "verify", 10)],
    )
    evidence = [EvidenceItem("ev_new", "config", "postgres config", "config", 0.95)]

    result = KnowledgeRefresher().refresh(finding, plan, evidence)
    assert result.refreshed
    assert result.finding.status == "verified"
    assert "ev_new" in result.finding.evidence_ids


def test_revalidation_executor_only_uses_registered_handlers():
    executor = RevalidationExecutor()
    executor.register(
        "inspect_config",
        lambda target: EvidenceItem("ev_1", "config", "verified", target, 0.9),
    )
    plan = RevalidationPlan(
        "fd_1",
        [
            RevalidationStep("inspect_config", "config", "verify", 10),
            RevalidationStep("unknown", "anything", "blocked", 1),
        ],
    )
    result = executor.execute(plan)
    assert len(result) == 1
    assert result[0].id == "ev_1"
