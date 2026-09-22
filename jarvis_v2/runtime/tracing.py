"""Audit integration for the JARVIS runtime lifecycle."""
from __future__ import annotations
from jarvis_v2.audit import AuditLog

class RuntimeTracer:
    def __init__(self, audit: AuditLog | None = None) -> None:
        self.audit=audit or AuditLog()

    def request(self, identity, request): return self.audit.append("request.received", identity, request)
    def plan(self, identity, request, plan): return self.audit.append("plan.created", identity, request, {"goal":plan.goal,"steps":len(plan.steps),"blocked":plan.blocked})
    def security(self, identity, request, decision): return self.audit.append("security.decision", identity, request, {"allowed":decision.allowed,"requires_confirmation":decision.requires_confirmation,"reason":decision.reason})
    def execution(self, identity, request, result): return self.audit.append("execution.completed", identity, request, {"success":result.success,"message":result.message})
    def error(self, identity, request, error): return self.audit.append("runtime.error", identity, request, {"error":str(error)})
