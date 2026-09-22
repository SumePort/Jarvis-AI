"""End-to-end secure runtime path for JARVIS V2."""
from __future__ import annotations
from dataclasses import dataclass
import inspect
from jarvis_v2.audit import AuditLog
from jarvis_v2.security import SecurityPolicy, IdentitySession
from jarvis_v2.actions.planner import ActionPlanner, ActionPlan, ActionPlannerBrain
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
    """Authoritative security gate around planning and closed-loop execution."""
    def __init__(self, planner: ActionPlanner, loop: AgentLoop,
                 brain: ActionPlannerBrain | None = None,
                 security: SecurityPolicy | None = None,
                 audit: AuditLog | None = None) -> None:
        self.planner=planner; self.loop=loop; self.brain=brain
        self.security=security or SecurityPolicy()
        self.tracer=RuntimeTracer(audit or AuditLog())

    def run(self, session: IdentitySession, request: str, context: dict,
            data_class: DataClass=DataClass.NORMAL, confirmed: bool=False,
            plan: ActionPlan | None=None) -> SecureRunResult:
        identity=session.identity
        self.tracer.request(identity, request)
        if not session.authenticated:
            d=self.security.authorize(identity, data_class, ActionRisk.DENY, False, confirmed)
            self.tracer.security(identity, request, d)
            return SecureRunResult(False, False, d.reason)
        try:
            if plan is None:
                if self.brain is not None:
                    plan=self.planner.from_brain(self.brain, request, context)
                elif hasattr(self.planner, "build"):
                    plan=self.planner.build(request, context)
                else:
                    return SecureRunResult(False, False, "No action plan, planner build method, or planner brain supplied")
            if hasattr(self.planner, "validate"):
                plan=self.planner.validate(plan)
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
            if not d.allowed: return SecureRunResult(False, d.requires_confirmation, d.reason)
            run_params = inspect.signature(self.loop.run).parameters
            if "confirmed" in run_params:
                execution=self.loop.run(plan, confirmed=confirmed)
            else:
                execution=self.loop.run(plan)
            verification = getattr(execution, "verification", None)
            if verification is not None:
                self.tracer.execution(identity, request, verification)
                return SecureRunResult(verification.success, False, verification.message, execution)
            success = bool(getattr(execution, "success", False))
            message = str(getattr(execution, "message", "Execution completed." if success else "Execution failed."))
            return SecureRunResult(success, False, message, execution)
        except Exception as exc:
            self.tracer.error(identity, request, exc)
            raise
