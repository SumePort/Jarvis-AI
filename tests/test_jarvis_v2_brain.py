from jarvis_v2.brain import JsonBrainAdapter
from jarvis_v2.core.types import ActionRisk

def test_json_brain_produces_structured_plan():
    def fake(prompt):
        return '{"goal":"open app","steps":[{"tool":"open_app","arguments":{"name":"notepad"},"risk":"allow","reason":"user requested it"}]}'
    plan=JsonBrainAdapter(fake).plan("open notepad", {})
    assert plan.goal == "open app"
    assert plan.steps[0].tool == "open_app"
    assert plan.steps[0].risk == ActionRisk.ALLOW
