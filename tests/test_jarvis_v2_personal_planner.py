from pathlib import Path

from jarvis_v2.personal.assistant import PersonalAssistant
from jarvis_v2.personal.conversation import JarvisConversation
from jarvis_v2.personal.planner import PersonalPlanner
from jarvis_v2.personal.tasks import TaskStore
from jarvis_v2.brain.provider import BrainResponse

class FakeBrain:
    def respond(self, request, context, observations): return BrainResponse(text="brain response")
    def plan(self, request, context): raise NotImplementedError


def test_planner_creates_task(tmp_path: Path):
    planner=PersonalPlanner(TaskStore(tmp_path/"tasks.json"))
    result=planner.plan("remind me to call dad tomorrow")
    assert result.intent == "create_task"
    assert result.tasks[0].title == "call dad"
    assert result.tasks[0].due_at is not None


def test_assistant_routes_conversation(tmp_path: Path):
    tasks=TaskStore(tmp_path/"tasks.json")
    conversation=JarvisConversation(FakeBrain())
    conversation.personal.tasks=tasks
    assistant=PersonalAssistant(FakeBrain(),conversation=conversation,planner=PersonalPlanner(tasks))
    assistant.authenticate()
    result=assistant.handle("hello Jarvis")
    assert result.mode == "conversation"
    assert result.conversation.response == "brain response"
