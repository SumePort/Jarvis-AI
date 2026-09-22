"""Strict JSON brain adapter for local or remote model clients."""
from __future__ import annotations
import json
from typing import Any, Callable
from jarvis_v2.actions import ActionPlan, ActionStep
from jarvis_v2.core.types import ActionRisk
from .provider import BrainResponse

class JsonBrainAdapter:
    """Accept model output only through a small, parseable action schema."""
    def __init__(self, model_call: Callable[[str], str]) -> None:
        self.model_call=model_call

    def _prompt(self, request: str, context: dict[str, Any]) -> str:
        return json.dumps({"request":request,"context":context,"required_output":{"goal":"string","steps":[{"tool":"string","arguments":"object","risk":"allow|confirm|deny","reason":"string"}]}}, ensure_ascii=False)

    def propose_actions(self, request: str, context: dict[str, Any], tools: list[Any]) -> ActionPlan:
        tool_context = [{"name": t.name, "description": t.description, "risk": t.risk.value, "data_class": t.data_class.value} for t in tools]
        context = {**context, "available_tools": tool_context}
        return self.plan(request, context)

    def plan(self, request: str, context: dict[str, Any]) -> ActionPlan:
        raw=self.model_call(self._prompt(request, context))
        data=json.loads(raw)
        steps=[]
        for item in data.get("steps", []):
            try: risk=ActionRisk(item.get("risk", "confirm"))
            except ValueError: risk=ActionRisk.CONFIRM
            steps.append(ActionStep(item["tool"], item.get("arguments", {}), risk, item.get("reason", "")))
        return ActionPlan(data.get("goal", request), steps)

    def respond(self, request: str, context: dict[str, Any], observations: list[dict[str, Any]]) -> BrainResponse:
        prompt=json.dumps({"request":request,"context":context,"observations":observations,"task":"answer the user concisely based on evidence"}, ensure_ascii=False)
        return BrainResponse(text=self.model_call(prompt), metadata={"provider":"json_brain"})
