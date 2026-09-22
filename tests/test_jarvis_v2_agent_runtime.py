from jarvis_v2.actions.executor import ActionExecutor
from jarvis_v2.actions.planner import ActionPlan, ActionPlanner, ActionStep
from jarvis_v2.core.types import ActionRisk, ToolSpec
from jarvis_v2.environment.observer import EnvironmentObserver
from jarvis_v2.knowledge.fabric import JarvisKnowledgeFabric
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph
from jarvis_v2.runtime.agent_runtime import JarvisAgentRuntime


def test_agent_runtime_runs_end_to_end():
    state = {"ready": False}
    def start():
        state["ready"] = True
    planner = ActionPlanner([ToolSpec("start", "start", risk=ActionRisk.ALLOW)])
    runtime = JarvisAgentRuntime(
        planner,
        ActionExecutor({"start": start}),
        JarvisKnowledgeFabric(UnifiedWorldGraph()),
        environment_observer=EnvironmentObserver(lambda: dict(state)),
    )
    result = runtime.run("start service", plan=ActionPlan("start service", [ActionStep("start", {}, ActionRisk.ALLOW)]))
    assert result.execution.verifications[-1].success
    assert state["ready"]


def test_agent_runtime_blocks_without_observer():
    planner = ActionPlanner([ToolSpec("start", "start", risk=ActionRisk.ALLOW)])
    runtime = JarvisAgentRuntime(planner, ActionExecutor({"start": lambda: None}), JarvisKnowledgeFabric(UnifiedWorldGraph()))
    result = runtime.run("start", plan=ActionPlan("start", [ActionStep("start", {}, ActionRisk.ALLOW)]))
    assert result.blocked
