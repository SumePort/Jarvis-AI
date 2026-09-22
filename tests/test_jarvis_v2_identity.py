from pathlib import Path

from jarvis_v2.brain.provider import BrainResponse
from jarvis_v2.personal.assistant import PersonalAssistant
from jarvis_v2.personal.conversation import JarvisConversation
from jarvis_v2.personal.identity import IdentityStore, IdentityDataPaths
from jarvis_v2.personal.context import PersonalContext
from jarvis_v2.personal.profile import PersonalProfileStore
from jarvis_v2.personal.tasks import TaskStore


class FakeBrain:
    def respond(self, request, context, observations):
        return BrainResponse(text=f"Hello {context['identity']['name']}")
    def plan(self, request, context):
        raise NotImplementedError


def test_identity_isolates_profile_and_tasks(tmp_path: Path):
    store = IdentityStore(tmp_path / "identities.json")
    alice = store.register("alice", "Alice", "1234")
    store.register("bob", "Bob", "5678")

    a = IdentityDataPaths("alice", tmp_path / "users")
    b = IdentityDataPaths("bob", tmp_path / "users")

    PersonalProfileStore(a.profile).save(__import__("jarvis_v2.personal.profile", fromlist=["PersonalProfile"]).PersonalProfile(name=alice.name))
    PersonalProfileStore(b.profile).save(__import__("jarvis_v2.personal.profile", fromlist=["PersonalProfile"]).PersonalProfile(name="Bob"))

    TaskStore(a.tasks).add("Alice task")
    TaskStore(b.tasks).add("Bob task")

    assert PersonalProfileStore(a.profile).load().name == "Alice"
    assert PersonalProfileStore(b.profile).load().name == "Bob"
    assert [t.title for t in TaskStore(a.tasks).all()] == ["Alice task"]
    assert [t.title for t in TaskStore(b.tasks).all()] == ["Bob task"]
    assert store.authenticate("alice", "1234").name == "Alice"


def test_assistant_switches_identity(tmp_path: Path):
    store = IdentityStore(tmp_path / "identities.json")
    conversation = JarvisConversation(FakeBrain(), identity_store=store)
    assistant = PersonalAssistant(FakeBrain(), conversation=conversation, identity_store=store)

    store.register("shubham", "Shubham", "1111")
    store.register("father", "Father", "2222")

    assistant.authenticate("shubham", "1111")
    assert assistant.conversation.session.identity_id == "shubham"
    assert assistant.handle("hello").conversation.response == "Hello Shubham"

    assistant.logout()
    assistant.authenticate("father", "2222")
    assert assistant.conversation.session.identity_id == "father"
    assert assistant.handle("hello").conversation.response == "Hello Father"
