from jarvis_v2.runtime.local import build_local_runtime


def test_local_runtime_assembles(monkeypatch):
    monkeypatch.setenv("JARVIS_MODEL_URL", "http://127.0.0.1:8080/v1")
    runtime, capabilities = build_local_runtime()
    assert runtime.brain is not None
    assert runtime.environment_observer is not None
    assert "calculate" in runtime.planner.tools
    assert capabilities.get("python") is not None
