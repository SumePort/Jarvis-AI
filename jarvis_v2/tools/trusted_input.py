"""Trusted UI handoff for sensitive fields.

This adapter intentionally never accepts a sensitive value. It pauses the
agent before a protected field and returns a resumable handoff request.
"""
from __future__ import annotations

from dataclasses import dataclass
from jarvis_v2.core.types import ToolSpec, ActionRisk, DataClass
from jarvis_v2.security.sensitive_input import SensitiveInputGate, SensitiveInputKind


@dataclass(frozen=True)
class SensitiveHandoff:
    request_id: str
    kind: str
    instruction: str
    application: str | None


class TrustedInputHandoff:
    def __init__(self, gate: SensitiveInputGate | None = None) -> None:
        self.gate = gate or SensitiveInputGate()

    def request_user_input(self, kind: str, instruction: str,
                           application: str | None = None) -> dict:
        try:
            input_kind = SensitiveInputKind(kind)
        except ValueError as exc:
            raise ValueError("Unsupported sensitive input kind") from exc
        request = self.gate.request(input_kind, instruction, application)
        return {
            "status": "WAITING_FOR_USER",
            "request_id": request.request_id,
            "kind": request.kind.value,
            "instruction": request.instruction,
            "application": request.application,
            "expires_at": request.expires_at,
        }

    def resume_after_user_input(self, request_id: str) -> dict:
        request = self.gate.complete(request_id)
        return {
            "status": "USER_INPUT_COMPLETED",
            "request_id": request.request_id,
            "kind": request.kind.value,
        }

    def cancel_user_input(self, request_id: str) -> dict:
        self.gate.cancel(request_id)
        return {"status": "USER_INPUT_CANCELLED", "request_id": request_id}


def trusted_input_specs() -> list[ToolSpec]:
    return [
        ToolSpec(
            "request_user_sensitive_input",
            "Pause JARVIS and ask the user to enter a sensitive value directly in the trusted application. Never provide the value to JARVIS.",
            {
                "kind": "string",
                "instruction": "string",
                "application": "string",
            },
            ("os.windows",),
            ActionRisk.CONFIRM,
            DataClass.PROTECTED,
        ),
        ToolSpec(
            "resume_after_user_sensitive_input",
            "Resume after the user reports that sensitive input was completed.",
            {"request_id": "string"},
            ("os.windows",),
            ActionRisk.ALLOW,
            DataClass.NORMAL,
        ),
        ToolSpec(
            "cancel_user_sensitive_input",
            "Cancel a pending sensitive input handoff.",
            {"request_id": "string"},
            ("os.windows",),
            ActionRisk.CONFIRM,
            DataClass.NORMAL,
        ),
    ]
