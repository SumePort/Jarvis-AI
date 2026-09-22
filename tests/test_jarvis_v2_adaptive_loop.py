from jarvis_v2.actions.executor import ActionExecutor
from jarvis_v2.actions.planner import ActionPlan, ActionPlanner, ActionStep
from jarvis_v2.core.types import ActionRisk, ToolSpec
from jarvis_v2.loop.controller import Verification
from jarvis_v2.loop.adaptive import AdaptiveAgentLoop


class R:
    def __init__(self):
        self.calls = 0
    def replan(self, goal, observations, previous):
        self.calls += 1
        return ActionPlan(goal, [ActionStep("check", {}, ActionRisk.ALLOW)])


def test_adaptive_loop_replans_after_failed_verification():
    state = {"n": 0}
    def check():
        state["n"] += 1
        return {"count": state["n"]}
    planner = ActionPlanner([ToolSpec("check", "check", risk=ActionRisk.ALLOW)])
    loop = AdaptiveAgentLoop(planner, ActionExecutor({"check": check}), max_iterations=3)
    replanner = R()
    def observer():
        return dict(state)
    def verifier(plan, actions, observed):
        return Verification(observed["count"] >= 2, "ok" if observed["count"] >= 2 else "not yet")
    result = loop.run(ActionPlan("reach two", [ActionStep("check", {}, ActionRisk.ALLOW)]), observer, verifier, replanner)
    assert result.verifications[-1].success
    assert result.iterations == 2
    assert replanner.calls == 1


def test_adaptive_loop_stops_on_confirmation():
    planner = ActionPlanner([ToolSpec("check", "check", risk=ActionRisk.CONFIRM)])
    loop = AdaptiveAgentLoop(planner, ActionExecutor({"check": lambda: None}))
    result = loop.run(ActionPlan("x", [ActionStep("check")]), lambda: {}, lambda *a: Verification(False, "confirm"), R())
    assert result.iterations == 1
    assert not result.replanned
