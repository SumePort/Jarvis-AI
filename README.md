# JARVIS AI

**Local-first personal AI computer agent for Windows.**

Jarvis runs from the existing repository as a local system: a local LLM is the baseline brain, deterministic computer tools handle real actions, project memory learns local codebases, Chrome provides an online path, and LiveKit provides the realtime voice layer.

## Architecture

```
User voice
  ↓
LiveKit WebRTC + turn detection + interruptions
  ↓
STT
  ↓
Jarvis Core
  ├── Router
  ├── Planner / Context
  ├── Local Brain (llama-server)
  └── Tool Executor
        ↓
Security Engine
  ├── ALLOW
  ├── CONFIRM
  └── RESTRICT
        ↓
Computer / Coding / Vision / Browser / Projects / Memory
        ↓
Jarvis response
  ↓
LiveKit TTS
```

LiveKit is the realtime voice transport/orchestration layer. It does not replace Jarvis Core. This keeps computer control, security, memory and local reasoning in the existing architecture.

## Core principles

- No cloud LLM is required for the Jarvis brain.
- The local model is accessed through an OpenAI-compatible `llama-server`.
- Online requests open Chrome rather than requiring a search API key.
- Destructive or external actions require confirmation.
- Restricted harmful/unauthorized categories are blocked centrally.
- Password authentication is enabled by default.
- Local conversation and project memory are stored in SQLite.
- LiveKit is used for realtime voice, turn detection and interruptions.

## LiveKit voice setup

The repository currently targets **LiveKit Agents 1.8.x**. The Python `voice.livekit_agent` module defines the `AgentServer` and JARVIS V2 voice session. LiveKit's current CLI is the recommended way to start it; the legacy `python -m voice.livekit_agent dev` command is deprecated.

### 1. Install the LiveKit CLI

On Windows:

```powershell
winget install LiveKit.LiveKitCLI
```

If it is already installed, update it before development:

```powershell
lk --version
```

### 2. Create/link a LiveKit project

Create a LiveKit Cloud project, then authenticate the CLI:

```powershell
lk cloud auth
```

A self-hosted LiveKit server can also be used.

### 3. Install Python dependencies

From this repository:

```powershell
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

### 4. Configure `.env`

Copy `.env.example` to `.env` and fill in:

```text
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

Keep the existing local model settings:

```text
LOCAL_LLM_URL=http://127.0.0.1:8080/v1
LOCAL_LLM_MODEL=local-model
```

### 5. Start the local brain

For the Qwen model used during development:

```powershell
llama-server -m "E:\\ULTRON\\models\\llm\\qwen2.5-0.5b-instruct-q4_k_m.gguf" --host 127.0.0.1 --port 8080
```

### 6. Start the LiveKit voice agent

Use the current LiveKit CLI and explicitly point it at the JARVIS entrypoint:

```powershell
.\\.venv\\Scripts\\Activate.ps1
lk agent dev voice/livekit_agent.py
```

For production-style local startup without development reload:

```powershell
lk agent start voice/livekit_agent.py
```

The old command below is intentionally not recommended because the Python CLI is deprecated:

```powershell
python -m voice.livekit_agent dev
```

### 7. Connect a voice client

With the agent running, join the LiveKit project using the Agent Console or another LiveKit client and target the `jarvis` agent.

The session provides:

- streaming microphone audio
- LiveKit audio turn detection
- interruption handling
- Deepgram STT by default
- JARVIS V2 as the authoritative reasoning/action layer
- local `llama-server` as the JARVIS brain
- Inworld TTS by default

## Voice model choice

The default STT is `deepgram/nova-3` and the default TTS is `inworld/inworld-tts-2` through LiveKit Inference. Change `LIVEKIT_STT_MODEL`, `LIVEKIT_TTS_MODEL`, and `LIVEKIT_TTS_VOICE` in `.env` to use other supported models.

Important: LiveKit improves realtime transport, endpointing/turn detection and interruption handling; transcription accuracy still depends heavily on the selected STT model.

## Text mode

The existing text interface remains available:

```powershell
python main.py
```

## First commands

```text
/help
/system
/open app notepad
/open app chrome
/calc 25 * 4
/learn E:\path\to\SumePort
/search latest Python release
/windows
/exit
```

Natural-language commands are handled by Jarvis Core.

## Security

Policy is centralized in `security/security_policy.py`.

- **ALLOW** — normal local actions.
- **CONFIRM** — destructive, external, publishing, upload, Git push, shutdown/restart, etc.
- **RESTRICT** — unauthorized access, credential theft, malware deployment, ransomware, data theft, security-control bypass, unauthorized surveillance/exfiltration, fraud/theft.

Unknown actions are restricted by default.

The local password is a session gate. It is not a security boundary against someone who already has full access to the Windows account, repository, or disk.

## Branch

`feature/jarvis-v2-foundation` contains the current JARVIS V2 foundation and realtime voice work. `main` remains separate until the branch is verified locally.
