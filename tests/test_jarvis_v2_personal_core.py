from pathlib import Path

from jarvis_v2.personal.profile import PersonalProfileStore
from jarvis_v2.personal.tasks import TaskStore
from jarvis_v2.personal.context import PersonalContext


def test_personal_profile_and_tasks_persist(tmp_path: Path):
    profile=PersonalProfileStore(tmp_path/"profile.json")
    profile.set_preference("theme","dark")
    profile.add_goal("build JARVIS")
    tasks=TaskStore(tmp_path/"tasks.json")
    task=tasks.add("finish personal core", priority="high")
    assert profile.load().preferences["theme"] == "dark"
    assert "build JARVIS" in profile.load().goals
    assert tasks.pending()[0].id == task.id
    tasks.complete(task.id)
    assert tasks.pending() == []


def test_personal_context_contains_profile_memory_and_tasks(tmp_path: Path):
    profile=PersonalProfileStore(tmp_path/"profile.json"); profile.add_note("User likes concise answers")
    tasks=TaskStore(tmp_path/"tasks.json"); tasks.add("test assistant")
    context=PersonalContext(profile=profile,tasks=tasks).build("assistant")
    assert context["profile"]["important_notes"] == ["User likes concise answers"]
    assert context["pending_tasks"][0]["title"] == "test assistant"
