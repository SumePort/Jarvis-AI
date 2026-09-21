# JARVIS AI

Local-first AI computer agent under active architectural refactor.

## Vision

Jarvis is designed to remain useful without cloud AI APIs or internet access. A local model provides the baseline intelligence; project intelligence, coding, computer-control, vision, memory, security, and browser capabilities are separate subsystems.

## Architecture

- Local Brain — OpenAI-compatible local model endpoint (for example llama-server).
- Project Brain — learns and indexes local projects such as SumePort.
- Coding Agent — plans, edits, runs, tests, and debugs local software.
- Computer Agent — Windows apps, files, keyboard, mouse, and system controls.
- Vision Agent — screenshots, OCR, and screen understanding.
- Chrome Agent — online research and interaction with authorized web applications.
- Memory — local project, conversation, system, decision, and research memory.
- Security — password authentication, centralized policy, confirmations, and audit logs.

## Development status

Phase 1 has started on branch refactor/v1-local-first. Existing functionality is being migrated incrementally rather than discarded.
