"""High-impact workflow state machine with automatic sensitive-input pauses."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from jarvis_v2.security.sensitive_input import SensitiveInputGate, SensitiveInputKind
from jarvis_v2.tools.sensitive_detector import SensitiveActionDetector, SensitiveStep


class WorkflowState(str, Enum):
    RUNNING = "running"
    WAITING_FOR_USER = "waiting_for_user"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class WorkflowTransition:
    state: WorkflowState
    message: str
    request_id: str | None = None


_KIND_MAP = {
    SensitiveStep.PIN: SensitiveInputKind.PIN,
    SensitiveStep.OTP: SensitiveInputKind.OTP,
    SensitiveStep.PASSWORD: SensitiveInputKind.PASSWORD,
    SensitiveStep.CVV: SensitiveInputKind.CVV,
    SensitiveStep.RECOVERY_CODE: SensitiveInputKind.RECOVERY_CODE,
    SensitiveStep.PAYMENT_AMOUNT: SensitiveInputKind.PAYMENT_AMOUNT,
    SensitiveStep.FINAL_AUTHORIZATION: SensitiveInputKind.PAYMENT_AMOUNT,
}


class HighImpactWorkflow:
    def __init__(self, detector: SensitiveActionDetector | None = None,
                 gate: SensitiveInputGate | None = None) -> None:
        self.detector = detector or SensitiveActionDetector()
        self.gate = gate or SensitiveInputGate()
        self.state = WorkflowState.RUNNING
        self._request_id: str | None = None

    def inspect_ui(self, evidence: str, application: str | None = None) -> WorkflowTransition:
        if self.state != WorkflowState.RUNNING:
            return WorkflowTransition(self.state, "Workflow is not running", self._request_id)
        detection = self.detector.detect(evidence, application)
        if detection.step == SensitiveStep.NONE:
            return WorkflowTransition(WorkflowState.RUNNING, "Continue workflow")
        kind = _KIND_MAP[detection.step]
        request = self.gate.request(
            kind,
            f"Please complete the {detection.step.value.replace('_', ' ')} directly in {application or 'the trusted application'}. Do not tell JARVIS the secret.",
            application,
        )
        self._request_id = request.request_id
        self.state = WorkflowState.WAITING_FOR_USER
        return WorkflowTransition(
            self.state,
            request.instruction,
            request.request_id,
        )

    def resume(self, request_id: str) -> WorkflowTransition:
        if self.state != WorkflowState.WAITING_FOR_USER or request_id != self._request_id:
            raise PermissionError("No matching sensitive-input handoff is waiting")
        self.gate.complete(request_id)
        self._request_id = None
        self.state = WorkflowState.RUNNING
        return WorkflowTransition(self.state, "User completed the sensitive step; resume workflow")

    def complete(self) -> WorkflowTransition:
        self.state = WorkflowState.COMPLETED
        return WorkflowTransition(self.state, "Workflow completed")

    def cancel(self) -> WorkflowTransition:
        if self._request_id:
            self.gate.cancel(self._request_id)
        self._request_id = None
        self.state = WorkflowState.CANCELLED
        return WorkflowTransition(self.state, "Workflow cancelled")
