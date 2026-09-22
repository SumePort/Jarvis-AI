from jarvis_v2.brain.provider import BrainResponse
from jarvis_v2.personal.assistant import PersonalAssistant
from jarvis_v2.personal.conversation import JarvisConversation
from jarvis_v2.personal.identity import IdentityStore
from jarvis_v2.voice.runtime import VoiceRuntime
from jarvis_v2.voice.assistant import VoiceAssistant


class FakeBrain:
    def respond(self, request, context, observations):
        return BrainResponse(text=f"Hello {context['identity']['name']}")
    def plan(self, request, context):
        raise NotImplementedError


def test_voice_assistant_connects_identity_and_tts(tmp_path):
    store = IdentityStore(tmp_path / "identities.json")
    store.register("shubham", "Shubham", "1111")
    assistant = PersonalAssistant(FakeBrain(), conversation=JarvisConversation(FakeBrain(), identity_store=store), identity_store=store)
    assistant.authenticate("shubham", "1111")

    spoken = []
    voice = VoiceRuntime(lambda: True, lambda: "hello Jarvis", spoken.append)
    result = VoiceAssistant(assistant, voice).listen_and_handle()

    assert result.assistant is not None
    assert result.assistant.conversation.response == "Hello Shubham"
    assert spoken == ["Hello Shubham"]


def test_voice_assistant_does_not_bypass_authentication():
    assistant = PersonalAssistant(FakeBrain())
    voice = VoiceRuntime(lambda: True, lambda: "hello Jarvis", lambda text: None)
    try:
        VoiceAssistant(assistant, voice).listen_and_handle()
    except PermissionError:
        pass
    else:
        raise AssertionError("Voice must not bypass authentication")
