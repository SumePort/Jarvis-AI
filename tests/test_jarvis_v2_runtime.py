from pathlib import Path
from jarvis_v2.actions import ActionExecutor, ActionPlan, ActionPlanner, ActionStep
from jarvis_v2.core.types import ActionRisk, ToolSpec
from jarvis_v2.projects.world_model import ProjectWorldModelBuilder
from jarvis_v2.runtime import JarvisRuntime
from jarvis_v2.memory import MemoryStore

def test_runtime_connects_pipeline(tmp_path: Path):
    (tmp_path/"requirements.txt").write_text("fastapi\n", encoding="utf-8")
    (tmp_path/"main.py").write_text("def login():\n    pass\n", encoding="utf-8")
    world=ProjectWorldModelBuilder().build(str(tmp_path))
    registry=[ToolSpec("calculate","calculate",ActionRisk.ALLOW)]
    runtime=JarvisRuntime(ActionPlanner(registry), ActionExecutor({"calculate": lambda expression: {"result":14}}), MemoryStore(tmp_path/"memory.jsonl"))
    result=runtime.run("calculate 2+3", ActionPlan("calculate", [ActionStep("calculate", {"expression":"2+3"}, ActionRisk.ALLOW)]), world, observer=lambda:{"done":True})
    assert result.execution.verification.success
    assert result.reasoning_context["user_request"] == "calculate 2+3"
    assert result.learned_memory_ids
