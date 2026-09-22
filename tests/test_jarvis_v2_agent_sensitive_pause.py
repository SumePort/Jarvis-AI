from jarvis_v2.loop.environment_loop import EnvironmentAgentLoop
from jarvis_v2.runtime.high_impact_workflow import WorkflowState


class FakeObserver:
    def __init__(self):
        self.n = 0
    def capture(self):
        self.n += 1
        return type("Obs", (), {"snapshot": {"windows": [{"title": "GPay", "text": "Enter UPI PIN"}]}, "changes": []})()
    def observe_change(self, before):
        return before


def test_agent_loop_stops_before_next_action_on_sensitive_ui():
    class Planner:
        def validate(self, plan): return plan
    class Executor:
        def execute(self, plan, confirmed=False):
            raise AssertionError("executor must not run on sensitive screen")
    plan = type("Plan", (), {"goal": "pay", "blocked": False})()
    loop = EnvironmentAgentLoop(Planner(), Executor(), FakeObserver())
    result = loop.run(plan, lambda *args: None)
    assert result.state == WorkflowState.WAITING_FOR_USER
    assert result.sensitive_request_id
