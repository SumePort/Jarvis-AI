"""Central permission gate used by Jarvis tools."""
from __future__ import annotations

from dataclasses import dataclass
from .security_policy import PolicyDecision, decide


@dataclass(frozen=True)
class PermissionResult:
    decision: PolicyDecision
    action: str
    reason: str


class PermissionEngine:
    def check(self, action: str) -> PermissionResult:
        decision = decide(action)
        reasons = {
            PolicyDecision.ALLOW: "Action is allowed by the Jarvis policy.",
            PolicyDecision.CONFIRM: "User confirmation is required before execution.",
            PolicyDecision.RESTRICT: "Action is restricted by the Jarvis policy.",
        }
        return PermissionResult(decision, action, reasons[decision])
