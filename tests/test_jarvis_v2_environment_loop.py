from jarvis_v2.actions.executor import ActionExecutor
from jarvis_v2.actions.planner import ActionPlan, ActionPlanner, ActionStep
from jarvis_v2.core.types import ActionRisk, ToolSpec
from jarvis_v2.environment.observer import EnvironmentObserver
from jarvis_v2.loop.controller import Verification
from jarvis_v2.loop.environment_loop import EnvironmentAgentLoop


def test_environment_observer_detects_changes():
    state = {"apps": []}
    observer = EnvironmentObserver(lambda: dict(state))
    before = observer.capture()
    state["apps"] = ["Chrome"]
    after = observer.observe_change(before)
    assert after.changes[0]["field"] == "apps"


def test_environment_loop_uses_observed_state():
    state = {"ready": False}
    def action():
        state["ready"] = True
    planner = ActionPlanner([ToolSpec("start", "start", risk=ActionRisk.ALLOW)])
    observer = EnvironmentObserver(lambda: dict(state))
    loop = EnvironmentAgentLoop(planner, ActionExecutor({"start": action}), observer)
    def verify(plan, actions, evidence):
        return Verification(evidence["snapshot"]["ready"], "ready")
    result = loop.run(ActionPlan("start", [ActionStep("start", {}, ActionRisk.ALLOW)]), verify)
    assert result.verifications[-1].success
