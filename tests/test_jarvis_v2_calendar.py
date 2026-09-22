from datetime import datetime, timezone, timedelta
from pathlib import Path

from jarvis_v2.personal.calendar import CalendarStore
from jarvis_v2.personal.reminders import ReminderStore
from jarvis_v2.personal.scheduler import ReminderScheduler
from jarvis_v2.personal.planner import PersonalPlanner


def test_calendar_and_reminder_are_persistent(tmp_path: Path):
    calendar = CalendarStore(tmp_path / "calendar.json")
    reminders = ReminderStore(tmp_path / "reminders.json")
    event = calendar.add("Dentist", "2030-01-02T10:00:00+00:00")
    reminder = reminders.add("Call dad", "2030-01-02T09:00:00+00:00")
    assert calendar.upcoming()[0].title == "Dentist"
    assert reminders.due(datetime(2030, 1, 2, 9, 1, tzinfo=timezone.utc))[0].text == "Call dad"


def test_scheduler_delivers_due_once(tmp_path: Path):
    store = ReminderStore(tmp_path / "reminders.json")
    reminder = store.add("Test", "2030-01-02T09:00:00+00:00")
    spoken = []
    scheduler = ReminderScheduler(store)
    result = scheduler.poll(datetime(2030, 1, 2, 9, 1, tzinfo=timezone.utc), spoken.append)
    assert result[0].delivered
    assert spoken[0].id == reminder.id
    assert scheduler.poll(datetime(2030, 1, 2, 9, 2, tzinfo=timezone.utc)) == []


def test_planner_creates_timed_reminder(tmp_path: Path):
    planner = PersonalPlanner(
        calendar=CalendarStore(tmp_path / "calendar.json"),
        reminders=ReminderStore(tmp_path / "reminders.json"),
    )
    result = planner.plan("remind me to call dad at 18:30")
    assert result.intent == "create_reminder"
    assert result.reminders[0].text == "call dad"
