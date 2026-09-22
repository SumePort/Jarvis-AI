from datetime import datetime, timezone
from pathlib import Path

from jarvis_v2.personal.calendar import CalendarStore
from jarvis_v2.personal.daily_planner import DailyPlanner
from jarvis_v2.personal.profile import PersonalProfile, PersonalProfileStore
from jarvis_v2.personal.tasks import TaskStore


def test_daily_planner_combines_profile_tasks_and_calendar(tmp_path: Path):
    profile = PersonalProfileStore(tmp_path / "profile.json")
    profile.save(PersonalProfile(
        name="Shubham",
        routines={"morning": "Study for 1 hour"},
        goals=["Finish SumePort milestone"],
        important_notes=["Keep focused"],
    ))
    tasks = TaskStore(tmp_path / "tasks.json")
    tasks.add("Finish milestone", due_at="2030-01-02", priority="high")
    tasks.add("Later task", due_at="2030-01-03", priority="normal")
    calendar = CalendarStore(tmp_path / "calendar.json")
    calendar.add("Team meeting", "2030-01-02T10:00:00+00:00")

    plan = DailyPlanner(profile, tasks, calendar).build(
        datetime(2030, 1, 2, tzinfo=timezone.utc).date()
    )
    assert plan.date == "2030-01-02"
    assert plan.tasks[0].title == "Finish milestone"
    assert plan.events[0].title == "Team meeting"
    assert plan.goals == ["Finish SumePort milestone"]
    assert plan.routines == ["Study for 1 hour"]
    assert plan.focus
