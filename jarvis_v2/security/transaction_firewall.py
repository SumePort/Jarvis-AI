"""Transaction firewall for high-impact local operations."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import time
import secrets
from typing import Any, Callable

from jarvis_v2.audit.log import AuditLog


@dataclass(frozen=True)
class TransactionIntent:
    transaction_id: str
    identity_id: str
    device_id: str
    operation: str
    amount: str | None
    destination: str | None
    summary: str
    intent_hash: str
    expires_at: float


@dataclass(frozen=True)
class TransactionApproval:
    transaction_id: str
    intent_hash: str
    approved_at: float
    expires_at: float


class TransactionFirewall:
    """Bind human approval to the exact transaction that will be executed.

    The firewall is intentionally independent from the model. A model can
    propose a transaction, but it cannot approve it, alter it after approval,
    retrieve protected credentials, or bypass the local approval boundary.
    """

    def __init__(self, audit: AuditLog | None = None, approval_ttl: float = 90.0):
        self.audit = audit or AuditLog("data/jarvis/transactions.jsonl")
        self.approval_ttl = max(10.0, approval_ttl)
        self._approvals: dict[str, TransactionApproval] = {}

    @staticmethod
    def _hash(operation: str, amount: str | None, destination: str | None, summary: str) -> str:
        payload = "\x1f".join([operation, amount or "", destination or "", summary])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def prepare(self, identity_id: str, device_id: str, operation: str,
                amount: str | None, destination: str | None, summary: str) -> TransactionIntent:
        if not identity_id or not device_id or not operation or not summary:
            raise ValueError("Transaction identity, device, operation and summary are required")
        now = time.time()
        transaction_id = "txn_" + secrets.token_hex(12)
        intent_hash = self._hash(operation, amount, destination, summary)
        intent = TransactionIntent(
            transaction_id, identity_id, device_id, operation, amount, destination,
            summary, intent_hash, now + self.approval_ttl,
        )
        self.audit.append(
            "transaction_prepared", identity_id, None,
            {"transaction_id": transaction_id, "operation": operation,
             "amount": amount, "destination": destination, "intent_hash": intent_hash},
        )
        return intent

    def approve(self, intent: TransactionIntent, identity_id: str, device_id: str,
                confirmation_phrase: str) -> TransactionApproval:
        if identity_id != intent.identity_id or device_id != intent.device_id:
            raise PermissionError("Transaction identity/device mismatch")
        if time.time() > intent.expires_at:
            raise PermissionError("Transaction approval window expired")
        if confirmation_phrase.strip().lower() not in {
            "confirm", "confirm payment", "approve", "yes, approve",
        }:
            raise PermissionError("Explicit transaction confirmation required")
        approval = TransactionApproval(
            intent.transaction_id, intent.intent_hash, time.time(),
            min(intent.expires_at, time.time() + self.approval_ttl),
        )
        self._approvals[intent.transaction_id] = approval
        self.audit.append(
            "transaction_approved", identity_id, None,
            {"transaction_id": intent.transaction_id, "intent_hash": intent.intent_hash},
        )
        return approval

    def execute(self, intent: TransactionIntent, approval: TransactionApproval,
                operation: Callable[[], Any]) -> Any:
        current_hash = self._hash(intent.operation, intent.amount, intent.destination, intent.summary)
        if approval.transaction_id != intent.transaction_id or approval.intent_hash != current_hash:
            raise PermissionError("Transaction changed after approval")
        if time.time() > approval.expires_at:
            raise PermissionError("Transaction approval expired")
        try:
            result = operation()
            self.audit.append(
                "transaction_executed", intent.identity_id, None,
                {"transaction_id": intent.transaction_id, "intent_hash": current_hash},
            )
            return result
        except Exception as exc:
            self.audit.append(
                "transaction_failed", intent.identity_id, None,
                {"transaction_id": intent.transaction_id, "error_type": type(exc).__name__},
            )
            raise
        finally:
            self._approvals.pop(intent.transaction_id, None)
