from jarvis_v2.voice import VoiceRuntime

def test_voice_runtime_wake_and_stt():
    spoken=[]
    runtime=VoiceRuntime(lambda: True, lambda: "open notepad", spoken.append)
    assert runtime.wait_for_wake()
    turn=runtime.listen_once()
    assert turn.transcript == "open notepad"
    runtime.speak("Done")
    assert spoken == ["Done"]
