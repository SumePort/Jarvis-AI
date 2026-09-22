from jarvis_v2.actions.planner import ActionPlan, ActionPlanner, ActionStep
from jarvis_v2.core.types import ActionRisk, ToolSpec
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph
from jarvis_v2.knowledge.fabric import JarvisKnowledgeFabric
from jarvis_v2.reasoning.action_reasoner import KnowledgeActionReasoner


def test_reasoner_uses_world_evidence():
    fabric = JarvisKnowledgeFabric(UnifiedWorldGraph())
    fabric.add_environment({"applications": [{"id": "chrome", "name": "Chrome"}]})
    reasoner = KnowledgeActionReasoner(fabric, ActionPlanner([]))
    decision = reasoner.prepare("open Chrome")
    assert "environment:applications:chrome" in decision.relevant_nodes


def test_reasoner_preserves_tool_safety():
    spec = ToolSpec("open_app", "Open app", risk=ActionRisk.CONFIRM)
    planner = ActionPlanner([spec])
    reasoner = KnowledgeActionReasoner(JarvisKnowledgeFabric(UnifiedWorldGraph()), planner)
    plan = ActionPlan("open", [ActionStep("open_app", {"name": "Chrome"}, ActionRisk.ALLOW)])
    decision = reasoner.validate_plan(reasoner.prepare("open Chrome"), plan)
    assert decision.plan.steps[0].risk == ActionRisk.CONFIRM
