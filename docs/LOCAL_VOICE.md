# Local Voice Mode

JARVIS V2 can run voice fully locally with Vosk STT, the existing local llama-server brain, and Piper TTS.

## Install

Inside the repository virtual environment:

```powershell
pip install sounddevice vosk
```

Piper is installed separately. Set these environment variables:

```powershell
$env:PIPER_EXE="C:\path\to\piper.exe"
$env:PIPER_MODEL="C:\path\to\voice.onnx"
$env:VOSK_MODEL_PATH="C:\path\to\vosk-model-small-en-us-0.15"
$env:JARVIS_MIC_DEVICE="1"
$env:JARVIS_ENABLE_VOICE="1"
```

If the microphone is the Windows default device, `JARVIS_MIC_DEVICE` can be omitted.

Optional settings:

```powershell
$env:JARVIS_WAKE_WORD="hey jarvis"
$env:JARVIS_VOICE_USER_ID="default"
$env:JARVIS_VOICE_DEVICE_ID="local-pc"
$env:JARVIS_VOICE_TIMEOUT="8"
$env:JARVIS_VOICE_SILENCE="1.15"
```

## Start

Start the local brain first:

```powershell
llama-server -m "E:\ULTRON\models\llm\qwen2.5-0.5b-instruct-q4_k_m.gguf" --host 127.0.0.1 --port 8080
```

Then, in another PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
$env:JARVIS_ENABLE_VOICE="1"
python -m jarvis_v2.runtime.launcher
```

Expected startup:

```
JARVIS V2
runtime=ready
doom=ready
voice=ready
wake=Hey Jarvis
voice=local Vosk + Piper
```

Say:

1. **Hey Jarvis**
2. Wait for JARVIS to listen.
3. Give the command, for example: **open notepad**
4. JARVIS processes it through the normal JARVIS V2 security/tool pipeline.
5. The response is spoken through Piper.

You can also say **Hey Jarvis, open notepad** in one utterance.

## Security

The local voice layer only supplies normal speech text to JARVIS. It does not collect passwords, PINs, OTPs, CVVs, recovery codes, or other sensitive values. High-impact workflows continue to use JARVIS's existing sensitive-input handoff and confirmation boundaries.

The default voice identity is a local trusted-device session. It is an identity/session binding, not biometric authentication.
