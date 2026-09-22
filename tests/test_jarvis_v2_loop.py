from jarvis_v2.actions import ActionExecutor, ActionPlan, ActionPlanner, ActionStep
from jarvis_v2.core.types import ActionRisk, ToolSpec
from jarvis_v2.loop import AgentLoop

def test_closed_loop_executes_and_observes():
    tools=[ToolSpec(name="open_app", description="open app", risk=ActionRisk.ALLOW)]
    planner=ActionPlanner(tools)
    executor=ActionExecutor({"open_app": lambda name: {"opened": name}})
    seen={"state":"ready"}
    result=AgentLoop(planner, executor).run(ActionPlan("open", [ActionStep("open_app", {"name":"notepad"}, ActionRisk.ALLOW)]), observer=lambda: seen)
    assert result.verification.success
    assert result.observations[0]["state"] == "ready"

def test_closed_loop_blocks_unconfirmed_action():
    tools=[ToolSpec(name="delete_file", description="delete", risk=ActionRisk.CONFIRM)]
    result=AgentLoop(ActionPlanner(tools), ActionExecutor({"delete_file": lambda path: True})).run(ActionPlan("delete", [ActionStep("delete_file", {"path":"x"})]))
    assert not result.verification.success
    assert result.actions[0].requires_confirmation
