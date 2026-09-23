# JARVIS-owned voice model

This is the training boundary for a future fully self-hosted JARVIS voice. The repository contains the dataset format, voice target and runtime adapter; it does not contain pretrained weights.

## Target voice

Use an original mature male cinematic-assistant voice: warm baritone, clear diction, restrained British-inspired accent, calm delivery, measured pauses and natural conversational prosody. This is a voice design target, not a clone of an actor or film performance.

## Build path

1. Collect licensed/consented recordings from a speaker who has authorized their use.
2. Add clean WAV clips to a dataset and register each clip with `VoiceDataset`.
3. Fine-tune a local TTS model on that corpus using a private GPU worker when available.
4. Export the resulting weights to the local `PiperTTS`-compatible provider or a future JARVIS TTS provider.
5. Evaluate intelligibility, latency, pronunciation, Hindi/Hinglish handling, prosody and interruption recovery.
6. Keep the resulting weights under JARVIS ownership; no runtime API is required.

The current PC should be treated as an inference/development machine, not as the place to train a serious speech model from scratch. Training can later run on an owned/private GPU worker through DOOM.

## Runtime

Set `PIPER_EXE` and `PIPER_MODEL` for the current local adapter. Set `JARVIS_VOICE_STT_MODEL` to a small local Whisper model when using the faster-whisper adapter.
