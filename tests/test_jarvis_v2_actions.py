from jarvis_v2.actions import ActionExecutor, ActionPlan, ActionPlanner, ActionStep
from jarvis_v2.core.types import ActionRisk, ToolSpec

def test_planner_cannot_downgrade_confirm_risk():
    tools=[ToolSpec(name="delete_file", description="delete", risk=ActionRisk.CONFIRM)]
    plan=ActionPlanner(tools).validate(ActionPlan("delete", [ActionStep("delete_file", {"path":"x"}, ActionRisk.ALLOW)]))
    assert plan.steps[0].risk == ActionRisk.CONFIRM

def test_executor_requires_confirmation():
    ex=ActionExecutor({"delete_file": lambda path: "deleted"})
    result=ex.execute(ActionPlan("delete", [ActionStep("delete_file", {"path":"x"}, ActionRisk.CONFIRM)]))
    assert result[0].requires_confirmation
