from jarvis_v2.core.context import JarvisContext
from jarvis_v2.core.types import EnvironmentSnapshot, Plan, PlanStep, ToolCall


def test_context_contains_structured_environment_without_screenshot_dependency():
    snapshot = EnvironmentSnapshot(
        timestamp=1.0,
        applications=[{"name": "VS Code", "pid": 10}],
        workspaces=[{"name": "SumePort", "root": "E:/SumePort"}],
        repositories=[{"root": "E:/SumePort", "branch": "main"}],
    )
    context = JarvisContext(user_request="Understand SumePort", environment=snapshot)
    payload = context.to_model_input()

    assert payload["environment"]["workspaces"][0]["name"] == "SumePort"
    assert payload["environment"]["repositories"][0]["branch"] == "main"
    assert "visual_evidence" in payload["environment"]


def test_plan_is_tool_facing_not_execution_facing():
    plan = Plan(
        goal="Open the SumePort workspace",
        steps=(PlanStep(id="1", purpose="Open workspace", tool_call=ToolCall("workspace.open", {"path": "E:/SumePort"})),),
    )
    assert plan.steps[0].tool_call.tool == "workspace.open"
