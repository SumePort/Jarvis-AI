"""End-to-end secure runtime path for JARVIS V2."""
from __future__ import annotations
from dataclasses import dataclass
from jarvis_v2.audit import AuditLog
from jarvis_v2.audit import AuditLog
from jarvis_v2.security import SecurityPolicy, IdentitySession
from jarvis_v2.reasoning.context import ReasoningContextBuilder
from jarvis_v2.actions.planner import ActionPlanner
from jarvis_v2.loop.controller import AgentLoop
from jarvis_v2.runtime.tracing import RuntimeTracer
from jarvis_v2.core.types import ActionRisk, DataClass

@dataclass
class SecureRunResult:
    allowed: bool
    requires_confirmation: bool
    reason: str
    execution: object | None = None

class SecureRunner:
    def __init__(self, planner: ActionPlanner, loop: AgentLoop, security: SecurityPolicy | None=None,
                 audit: AuditLog | None=None) -> None:
        self.planner=planner
        self.loop=loop
        self.security=security or SecurityPolicy()
        self.tracer=RuntimeTracer(audit or AuditLog())

    def run(self, session: IdentitySession, request: str, context: dict,
            data_class: DataClass=DataClass.NORMAL, confirmed: bool=False) -> SecureRunResult:
        identity=session.identity
        self.tracer.request(identity, request)
        if not session.authenticated:
            d=self.security.authorize(identity, data_class, ActionRisk.DENY, False, confirmed)
            self.tracer.security(identity, request, d)
            return SecureRunResult(False, False, d.reason)
        try:
            plan=self.planner.build(request, context)
            self.tracer.plan(identity, request, plan)
            if plan.blocked:
                d=self.security.authorize(identity, data_class, ActionRisk.DENY, True, confirmed)
                self.tracer.security(identity, request, d)
                return SecureRunResult(False, False, "Plan blocked: " + "; ".join(plan.warnings))
            highest=ActionRisk.ALLOW
            if any(s.risk == ActionRisk.DENY for s in plan.steps): highest=ActionRisk.DENY
            elif any(s.risk == ActionRisk.CONFIRM for s in plan.steps): highest=ActionRisk.CONFIRM
            d=self.security.authorize(identity, data_class, highest, True, confirmed)
            self.tracer.security(identity, request, d)
            if not d.allowed:
                return SecureRunResult(False, d.requires_confirmation, d.reason)
            execution=self.loop.run(plan)
            self.tracer.execution(identity, request, execution)
            return SecureRunResult(True, False, "Execution completed", execution)
        except Exception as exc:
            self.tracer.error(identity, request, exc)
            raise
