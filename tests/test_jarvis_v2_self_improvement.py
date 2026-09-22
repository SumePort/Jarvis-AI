import pytest
from jarvis_v2.self_improvement.orchestrator import SelfImprovementOrchestrator

def test_self_improvement_blocks_protected_paths(tmp_path):
    from jarvis_v2.self_improvement.engine import SelfImprovementEngine
    engine = SelfImprovementEngine(str(tmp_path))
    orchestrator = SelfImprovementOrchestrator(engine)
    with pytest.raises(PermissionError):
        orchestrator._validate_paths(["jarvis_v2/security/policy.py"])

def test_self_improvement_blocks_path_escape(tmp_path):
    from jarvis_v2.self_improvement.engine import SelfImprovementEngine
    orchestrator = SelfImprovementOrchestrator(SelfImprovementEngine(str(tmp_path)))
    with pytest.raises(PermissionError):
        orchestrator._validate_paths(["../outside.py"])
