# JARVIS AI

**Local-first personal AI computer agent for Windows.**

Jarvis runs from the existing repository as a local system: a local LLM is the baseline brain, deterministic computer tools handle real actions, project memory learns local codebases, and Chrome provides an online path when internet access is available.

## Final architecture

```
User
  ↓
Authentication
  ↓
Jarvis Core
  ├── Router
  ├── Planner / Context
  └── Tool Executor
        ↓
Security Engine
  ├── ALLOW
  ├── CONFIRM
  └── RESTRICT
        ↓
  ┌──────────────┬──────────────┬──────────────┬──────────────┐
  Local Brain    Computer       Coding         Projects
  Vision         Browser/Chrome Memory         Voice
```

## Core principles

- No cloud AI API is required for the core.
- The local model is accessed through an OpenAI-compatible `llama-server`.
- Online requests open Chrome rather than requiring a Google/Gemini/OpenAI search API.
- Destructive or external actions require confirmation.
- Restricted harmful/unauthorized categories are blocked centrally.
- Password authentication is enabled by default.
- Local conversation and project memory are stored in SQLite.
- Old Gemini/LiveKit/LangChain runtime code has been removed from the active architecture.

## Hardware target

The repository is designed to work on modest Windows hardware with a CPU-compatible quantized local model. For this machine, keep the local model small enough for available RAM.

## Start Jarvis

### 1. Clone and enter the repository

```powershell
git clone https://github.com/SumePort/Jarvis-AI.git
cd Jarvis-AI
git checkout refactor/v1-local-first
```

### 2. Create the virtual environment

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure local model

Copy `.env.example` to `.env`.

Start your OpenAI-compatible local `llama-server` on port 8080. For example, with the Qwen model already used during development:

```powershell
llama-server -m "E:\ULTRON\models\llm\qwen2.5-0.5b-instruct-q4_k_m.gguf" --host 127.0.0.1 --port 8080
```

If your model/server is elsewhere, change `LOCAL_LLM_URL` and `LOCAL_LLM_MODEL` in `.env`.

### 4. Start Jarvis

Open a second PowerShell in the repository:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

On the first run Jarvis asks you to create a local password. Later runs ask for that password.

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

Natural language such as `Explain this project` is sent to the local brain.

## Project learning

Use:

```text
/learn E:\path\to\SumePort
```

Jarvis scans the project while ignoring Git, virtual environments, node_modules and generated build caches, then stores the project snapshot in local SQLite memory.

## Online layer

`/search <query>` opens Google in Chrome. This does not require a search API key. Browser navigation and interaction are separate modules so browser automation can grow without coupling it to the local brain.

## Security

Policy is centralized in `security/security_policy.py`.

- **ALLOW** — normal local actions.
- **CONFIRM** — destructive, external, publishing, upload, Git push, shutdown/restart, etc.
- **RESTRICT** — unauthorized access, credential theft, malware deployment, ransomware, data theft, security-control bypass, unauthorized surveillance/exfiltration, fraud/theft.

Unknown actions are restricted by default.

The local password is a session gate. It is not a security boundary against someone who already has full access to the Windows account, repository, or disk.

## Important

The branch `refactor/v1-local-first` is the active refactor branch. `main` is kept separate until this branch is verified locally.
