from jarvis_v2.brain.provider import BrainResponse
from jarvis_v2.personal.conversation import JarvisConversation

class FakeBrain:
    def respond(self, request, context, observations):
        return BrainResponse(text=f"I heard: {request}", metadata={"test": True})
    def plan(self, request, context):
        raise NotImplementedError


def test_conversation_requires_authentication():
    chat=JarvisConversation(FakeBrain())
    try:
        chat.handle("hello")
    except PermissionError:
        pass
    else:
        raise AssertionError("unauthenticated conversation was accepted")


def test_conversation_preserves_turns_and_personal_memory(tmp_path):
    from jarvis_v2.memory.store import MemoryStore
    from jarvis_v2.personal.context import PersonalContext
    from jarvis_v2.personal.memory import PersonalMemory
    from jarvis_v2.personal.profile import PersonalProfileStore
    from jarvis_v2.personal.tasks import TaskStore

    memory=PersonalMemory(MemoryStore(tmp_path/"memory.jsonl"))
    personal=PersonalContext(memory=memory.store, profile=PersonalProfileStore(tmp_path/"profile.json"), tasks=TaskStore(tmp_path/"tasks.json"))
    chat=JarvisConversation(FakeBrain(), personal=personal, memory=memory)
    chat.authenticate()
    result=chat.handle("I prefer dark mode")
    assert result.response == "I heard: I prefer dark mode"
    assert len(chat.turns) == 2
    assert memory.recall("dark mode")[0].kind == "preference"
    result=chat.handle("hello again")
    assert len(result.context["conversation"]) == 2
