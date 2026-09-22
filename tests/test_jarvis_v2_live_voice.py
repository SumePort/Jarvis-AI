from jarvis_v2.actions.executor import ActionExecutor
from jarvis_v2.actions.planner import ActionPlan, ActionPlanner, ActionStep
from jarvis_v2.core.types import ActionRisk, ToolSpec
from jarvis_v2.environment.observer import EnvironmentObserver
from jarvis_v2.knowledge.fabric import JarvisKnowledgeFabric
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph
from jarvis_v2.runtime.agent_runtime import JarvisAgentRuntime
from jarvis_v2.voice.live_agent import LiveVoiceAgent
from jarvis_v2.voice.runtime import VoiceRuntime


def test_live_voice_agent_wake_auth_and_execute():
    state = {"awake": False}
    voice = VoiceRuntime(lambda: True, lambda: "start", lambda text: state.update(awake=True))
    planner = ActionPlanner([ToolSpec("start", "start", risk=ActionRisk.ALLOW)])
    runtime = JarvisAgentRuntime(
        planner,
        ActionExecutor({"start": lambda: state.update(awake=True)}),
        JarvisKnowledgeFabric(UnifiedWorldGraph()),
        environment_observer=EnvironmentObserver(lambda: dict(state)),
    )
    agent = LiveVoiceAgent(runtime, voice, lambda: True)
    result = agent.run_once()
    assert result.agent is not None
    assert result.agent.execution.verifications[-1].success
    assert state["awake"]


def test_live_voice_agent_refuses_unauthenticated():
    voice = VoiceRuntime(lambda: True, lambda: "start", lambda text: None)
    planner = ActionPlanner([ToolSpec("start", "start", risk=ActionRisk.ALLOW)])
    runtime = JarvisAgentRuntime(
        planner,
        ActionExecutor({"start": lambda: None}),
        JarvisKnowledgeFabric(UnifiedWorldGraph()),
        environment_observer=EnvironmentObserver(lambda: {}),
    )
    agent = LiveVoiceAgent(runtime, voice, lambda: False)
    result = agent.run_once()
    assert result.agent is None
    assert result.metadata["authenticated"] is False
