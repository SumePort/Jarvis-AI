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

The LiveKit Agents framework supports realtime voice sessions with STT, LLM/TTS pipelines, turn detection and interruptions. The current implementation keeps the Jarvis brain local while using LiveKit for the voice layer.

### 1. Install the LiveKit CLI

On Windows:

```powershell
winget install LiveKit.LiveKitCLI
```

### 2. Create/link a LiveKit project

Create a LiveKit Cloud project, then authenticate the CLI:

```powershell
lk cloud auth
```

The LiveKit quickstart uses a free Cloud project for development and provides the project credentials needed by the agent. A self-hosted LiveKit server can also be used.

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

In a second PowerShell:

```powershell
.\\.venv\\Scripts\\Activate.ps1
python -m voice.livekit_agent
```

For LiveKit development mode, the CLI can also run the agent:

```powershell
lk agent dev
```

Then open the LiveKit Agent Console and start a session with the `jarvis` agent.

## Voice model choice

The default STT is `deepgram/nova-3` and the default TTS is `inworld/inworld-tts-2` through LiveKit Inference. Change `LIVEKIT_STT_MODEL`, `LIVEKIT_TTS_MODEL`, and `LIVEKIT_TTS_VOICE` in `.env` to use other supported models.

Important: LiveKit improves the realtime transport, endpointing/turn detection and interruption experience; transcription accuracy still depends heavily on the selected STT model.

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

`refactor/v1-local-first` is the active refactor branch. `main` remains separate until the branch is verified locally.
