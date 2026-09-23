# Self-hosted JARVIS voice

JARVIS now has a provider-neutral local voice boundary. The goal is to remove per-minute voice APIs without coupling the assistant to one speech vendor.

```text
microphone -> local VAD -> local STT -> JARVIS V2 -> local TTS -> speaker
                              |               |
                         conversation       DOOM
                              |
                         persistent memory
```

## Current foundation

- `jarvis_v2/voice/profile.py` defines the original male cinematic voice target.
- `jarvis_v2/voice/providers.py` provides optional local faster-whisper STT and Piper TTS adapters.
- `jarvis_v2/voice/engine.py` provides the injected realtime turn loop and interruption boundary.
- `jarvis_v2/voice/training/dataset.py` provides a safe JSONL voice-corpus manifest.

The model weights are intentionally not committed to Git. They are large binary artifacts and should remain in local/private storage.

## Why this is staged

A genuinely high-quality custom STT/TTS model cannot responsibly be trained from scratch on a low-memory CPU machine. We first establish the complete runtime and data boundary, then fine-tune/train the speech models on a private GPU worker through DOOM. That keeps the final system self-hosted while avoiding a dependency on a commercial voice API.

## Human-like behavior target

The voice engine is designed around streaming turns, barge-in, concise responses, natural pauses, multilingual/Hinglish support and an original mature male voice. The conversational intelligence remains in JARVIS V2 rather than inside the speech model.
