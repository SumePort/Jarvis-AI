from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jarvis_v2.personal.automation import Automation, AutomationEngine, AutomationStore
from jarvis_v2.personal.daily_planner import DailyPlanner


@dataclass
class AutomationResult:
    automation: Automation
    result: Any


class PersonalAutomation:
    """Identity-scoped automation facade for safe recurring assistant workflows."""

    def __init__(self, store: AutomationStore, daily_planner: DailyPlanner | None = None):
        self.store = store
        self.daily_planner = daily_planner
        self.handlers = {
            "daily_briefing": self._daily_briefing,
        }
        self.engine = AutomationEngine(store, self.handlers)

    def add_daily_briefing(self, name: str = "Daily briefing") -> Automation:
        return self.store.add(name, "daily", "daily_briefing")

    def run_due(self):
        return self.engine.run_due()

    def _daily_briefing(self, automation: Automation):
        if not self.daily_planner:
            return {"automation_id": automation.id, "status": "skipped", "reason": "daily planner unavailable"}
        plan = self.daily_planner.build()
        return {"automation_id": automation.id, "status": "ready", "plan": plan.to_dict()}
