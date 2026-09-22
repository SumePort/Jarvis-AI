from jarvis_v2.runtime.agent_runtime import JarvisAgentRuntime


def test_runtime_exposes_resume_and_cancel():
    assert hasattr(JarvisAgentRuntime, "resume")
    assert hasattr(JarvisAgentRuntime, "cancel")
    assert hasattr(JarvisAgentRuntime, "pending_workflows")
