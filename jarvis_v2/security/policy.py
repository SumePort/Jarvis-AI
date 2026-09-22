"""High-assurance authorization policy for JARVIS actions and protected data."""
from __future__ import annotations
from dataclasses import dataclass
from jarvis_v2.core.types import ActionRisk, DataClass


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    requires_confirmation: bool = False
    requires_user_input: bool = False
    reason: str = ""


class SecurityPolicy:
    def authorize(self, identity: str | None, data_class: DataClass, risk: ActionRisk,
                  authenticated: bool = False, explicit_confirmation: bool = False) -> AuthorizationDecision:
        if not identity or not authenticated:
            return AuthorizationDecision(False, reason="Authenticated identity required")
        if risk == ActionRisk.DENY:
            return AuthorizationDecision(False, reason="Action is denied by policy")

        if data_class == DataClass.PROTECTED:
            if not explicit_confirmation:
                return AuthorizationDecision(
                    False, requires_confirmation=True,
                    reason="Protected data requires explicit confirmation",
                )
            return AuthorizationDecision(
                True, requires_user_input=True,
                reason="Protected operation requires user entry at the trusted UI",
            )

        if risk == ActionRisk.CONFIRM and not explicit_confirmation:
            return AuthorizationDecision(False, requires_confirmation=True, reason="Explicit confirmation required")
        return AuthorizationDecision(True, reason="Authorized")
