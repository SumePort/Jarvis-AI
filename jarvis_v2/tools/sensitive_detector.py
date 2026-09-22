"""Deterministic sensitive-action detection from structured UI evidence."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re


class SensitiveStep(str, Enum):
    NONE = "none"
    PAYMENT_AMOUNT = "payment_amount"
    PIN = "pin"
    OTP = "otp"
    PASSWORD = "password"
    CVV = "cvv"
    RECOVERY_CODE = "recovery_code"
    FINAL_AUTHORIZATION = "final_authorization"


@dataclass(frozen=True)
class SensitiveDetection:
    step: SensitiveStep
    reason: str
    application: str | None = None


_PATTERNS = {
    SensitiveStep.PIN: (r"\bupi\s*pin\b", r"\bpin\b", r"enter.*pin"),
    SensitiveStep.OTP: (r"\botp\b", r"one[- ]time password", r"verification code"),
    SensitiveStep.PASSWORD: (r"\bpassword\b", r"enter.*password"),
    SensitiveStep.CVV: (r"\bcvv\b", r"security code"),
    SensitiveStep.RECOVERY_CODE: (r"recovery code", r"backup code"),
    SensitiveStep.PAYMENT_AMOUNT: (r"enter.*amount", r"payment amount", r"amount to pay"),
    SensitiveStep.FINAL_AUTHORIZATION: (r"confirm.*payment", r"place order", r"submit.*payment", r"authorize.*transaction"),
}


class SensitiveActionDetector:
    def detect(self, evidence: str, application: str | None = None) -> SensitiveDetection:
        text = re.sub(r"\s+", " ", evidence or "").strip().lower()
        if not text:
            return SensitiveDetection(SensitiveStep.NONE, "No UI evidence")
        # More sensitive credential prompts take precedence over generic actions.
        for step in (
            SensitiveStep.PIN, SensitiveStep.OTP, SensitiveStep.PASSWORD,
            SensitiveStep.CVV, SensitiveStep.RECOVERY_CODE,
            SensitiveStep.PAYMENT_AMOUNT, SensitiveStep.FINAL_AUTHORIZATION,
        ):
            for pattern in _PATTERNS[step]:
                if re.search(pattern, text):
                    return SensitiveDetection(step, f"Matched protected UI pattern: {step.value}", application)
        return SensitiveDetection(SensitiveStep.NONE, "No protected UI pattern matched", application)
