from datetime import datetime, timezone
from pathlib import Path

from jarvis_v2.personal.automation import AutomationEngine, AutomationStore
from jarvis_v2.personal.automation_service import PersonalAutomation


def test_daily_automation_runs_once(tmp_path: Path):
    store = AutomationStore(tmp_path / "automations.json")
    calls = []
    store.add("Test", "daily", "work")
    engine = AutomationEngine(store, {"work": lambda item: calls.append(item.name) or "ok"})
    now = datetime(2030, 1, 2, 9, tzinfo=timezone.utc)
    assert engine.run_due(now) == ["ok"]
    assert calls == ["Test"]
    assert engine.run_due(now) == []


def test_daily_briefing_automation(tmp_path: Path):
    store = AutomationStore(tmp_path / "automations.json")
    automation = PersonalAutomation(store)
    item = automation.add_daily_briefing()
    assert item.trigger == "daily"
    assert item.action == "daily_briefing"
