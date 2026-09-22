"""Application-aware high-impact UI detector."""
from __future__ import annotations
from dataclasses import dataclass
from jarvis_v2.tools.sensitive_detector import SensitiveStep


@dataclass(frozen=True)
class ApplicationWorkflow:
    name: str
    keywords: tuple[str, ...]
    sensitive_labels: tuple[str, ...]


DEFAULT_WORKFLOWS = (
    ApplicationWorkflow("upi", ("gpay", "google pay", "phonepe", "paytm", "upi"),
                         ("upi pin", "enter pin", "verify payment", "pay now")),
    ApplicationWorkflow("banking", ("bank", "netbanking", "internet banking"),
                         ("otp", "transaction password", "profile password", "authorize")),
    ApplicationWorkflow("trading", ("zerodha", "groww", "upstox", "angel", "trading", "broker"),
                         ("place order", "confirm order", "otp", "buy", "sell", "final authorization")),
    ApplicationWorkflow("billing", ("bill", "electricity", "recharge", "checkout"),
                         ("otp", "pin", "cvv", "pay now", "confirm payment")),
)


class ApplicationSensitiveDetector:
    """Adds deterministic application context without inspecting secret values."""

    def __init__(self, workflows=DEFAULT_WORKFLOWS):
        self.workflows = tuple(workflows)

    def detect(self, application: str, evidence: str) -> SensitiveStep:
        haystack = f"{application} {evidence}".lower()
        for workflow in self.workflows:
            if any(k in haystack for k in workflow.keywords):
                if any(k in haystack for k in ("upi pin", "enter pin", "transaction password")):
                    return SensitiveStep.PIN
                if "otp" in haystack:
                    return SensitiveStep.OTP
                if "cvv" in haystack:
                    return SensitiveStep.CVV
                if any(k in haystack for k in ("password", "recovery")):
                    return SensitiveStep.PASSWORD
                if any(k in haystack for k in ("place order", "confirm order", "pay now", "final authorization")):
                    return SensitiveStep.FINAL_AUTHORIZATION
        return SensitiveStep.NONE
