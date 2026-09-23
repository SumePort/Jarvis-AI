from pathlib import Path
from jarvis_v2.voice.engine import LocalVoiceEngine, VoiceEngineConfig
from jarvis_v2.voice.profile import JARVIS_MALE_PROFILE
from jarvis_v2.voice.training.dataset import VoiceDataset, VoiceSample
class FakeSTT:
    def transcribe(self,audio_path): return "hello jarvis"
class FakeTTS:
    def synthesize(self,text,output_path): Path(output_path).write_bytes(b"RIFF"); return output_path
def test_voice_profile_is_original_male_profile():
    assert JARVIS_MALE_PROFILE.gender=="male"; assert "actor" in JARVIS_MALE_PROFILE.accent
def test_voice_engine_uses_injected_providers(tmp_path):
    engine=LocalVoiceEngine(VoiceEngineConfig(language="en"),FakeSTT(),FakeTTS()); assert engine.transcribe("input.wav")=="hello jarvis"; assert Path(engine.speak("Hello.",str(tmp_path/"out.wav"))).exists(); assert "JARVIS" in engine.conversational_style_prompt()
def test_voice_dataset_round_trip(tmp_path):
    dataset=VoiceDataset(tmp_path); dataset.add(VoiceSample(audio="sample.wav",text="Hello, I am Jarvis.")); assert dataset.samples()[0].text=="Hello, I am Jarvis."
