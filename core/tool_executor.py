"""Central execution gate: policy -> confirmation -> tool -> audit."""
from __future__ import annotations

from security.audit_log import AuditLog
from security.confirmations import confirm
from security.permissions import PermissionEngine
from security.security_policy import PolicyDecision

class ToolExecutor:
    def __init__(self, permissions=None, audit=None):
        self.permissions = permissions or PermissionEngine()
        self.audit = audit or AuditLog()

    def run(self, action: str, fn, *args, description: str = "", **kwargs):
        permission = self.permissions.check(action)
        if permission.decision is PolicyDecision.RESTRICT:
            self.audit.record(action, "restricted", permission.reason)
            return f"Blocked: {permission.reason}"
        if permission.decision is PolicyDecision.CONFIRM:
            if not confirm(action, description or action):
                self.audit.record(action, "cancelled", "User declined confirmation.")
                return "Cancelled."
        try:
            result = fn(*args, **kwargs)
            self.audit.record(action, "success", str(result)[:500])
            return result
        except Exception as exc:
            self.audit.record(action, "error", repr(exc))
            return f"Error while executing {action}: {exc}"
