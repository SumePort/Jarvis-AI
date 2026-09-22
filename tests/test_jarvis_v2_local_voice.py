from jarvis_v2.voice.local import LocalWakeWordRuntime


class FakeRecognizer:
    def __init__(self, values):
        self.values = iter(values)

    def listen(self, **kwargs):
        return next(self.values)


def test_local_voice_keeps_command_from_wake_utterance():
    spoken = []
    voice = LocalWakeWordRuntime(
        FakeRecognizer(["noise", "Hey Jarvis open notepad"]),
        __import__("jarvis_v2.voice.local", fromlist=["WakeWord"]).WakeWord(),
        tts=spoken.append,
    )

    assert not voice.wait_for_wake()
    assert voice.wait_for_wake()
    assert voice.listen_once().transcript == "open notepad"
    voice.speak("Done")
    assert spoken == ["Done"]
