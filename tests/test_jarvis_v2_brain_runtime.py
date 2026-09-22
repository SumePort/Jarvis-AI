from jarvis_v2.actions.executor import ActionExecutor
from jarvis_v2.actions.planner import ActionPlan, ActionPlanner, ActionStep
from jarvis_v2.brain.json_brain import JsonBrainAdapter
from jarvis_v2.core.types import ActionRisk, ToolSpec
from jarvis_v2.environment.observer import EnvironmentObserver
from jarvis_v2.knowledge.fabric import JarvisKnowledgeFabric
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph
from jarvis_v2.runtime.agent_runtime import JarvisAgentRuntime


def test_json_brain_can_plan_and_runtime_can_execute():
    state = {"ready": False}

    def start():
        state["ready"] = True

    def model(prompt: str) -> str:
        return '{"goal":"start service","steps":[{"tool":"start","arguments":{},"risk":"allow","reason":"start it"}]}'

    planner = ActionPlanner([ToolSpec("start", "start", risk=ActionRisk.ALLOW)])
    runtime = JarvisAgentRuntime(
        planner,
        ActionExecutor({"start": start}),
        JarvisKnowledgeFabric(UnifiedWorldGraph()),
        brain=JsonBrainAdapter(model),
        environment_observer=EnvironmentObserver(lambda: dict(state)),
    )
    result = runtime.run("start service")
    assert result.execution.verifications[-1].success
    assert state["ready"]


def test_runtime_replans_through_brain_when_first_action_fails():
    state = {"ready": False, "attempts": 0}

    def first():
        state["attempts"] += 1
        raise RuntimeError("temporary failure")

    def second():
        state["ready"] = True

    calls = []

    def model(prompt: str) -> str:
        calls.append(prompt)
        if len(calls) == 1:
            return '{"goal":"start service","steps":[{"tool":"first","arguments":{},"risk":"allow"}]}'
        return '{"goal":"start service","steps":[{"tool":"second","arguments":{},"risk":"allow"}]}'

    planner = ActionPlanner([
        ToolSpec("first", "first", risk=ActionRisk.ALLOW),
        ToolSpec("second", "second", risk=ActionRisk.ALLOW),
    ])
    runtime = JarvisAgentRuntime(
        planner,
        ActionExecutor({"first": first, "second": second}),
        JarvisKnowledgeFabric(UnifiedWorldGraph()),
        brain=JsonBrainAdapter(model),
        environment_observer=EnvironmentObserver(lambda: dict(state)),
        max_iterations=2,
    )
    result = runtime.run("start service")
    assert result.execution.replanned
    assert result.execution.verifications[-1].success
    assert state["ready"]
    assert len(calls) == 2
