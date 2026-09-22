"""Build the integrated local JARVIS V2 runtime."""
from __future__ import annotations

import os

from jarvis_v2.capabilities import CapabilityRegistry
from jarvis_v2.environment.collector import JarvisEnvironment
from jarvis_v2.environment.observer import EnvironmentObserver
from jarvis_v2.knowledge.fabric import JarvisKnowledgeFabric
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph
from jarvis_v2.models.gateway import ModelGateway, ModelProfile, llama_cpp_client
from jarvis_v2.models.brain_factory import GatewayBrainFactory
from jarvis_v2.runtime.agent_runtime import JarvisAgentRuntime
from jarvis_v2.tools.runtime_registry import RuntimeToolRegistry
from jarvis_v2.actions.planner import ActionPlanner
from jarvis_v2.runtime.high_impact_workflow import HighImpactWorkflow
from jarvis_v2.security.sensitive_input import SensitiveInputGate
from jarvis_v2.tools.sensitive_detector import SensitiveActionDetector
from jarvis_v2.security.policy import SecurityPolicy
from jarvis_v2.audit.log import AuditLog
from jarvis_v2.devices.session_manager import DeviceSessionManager
from jarvis_v2.doom.session_bridge import DoomSessionBridge
from jarvis_v2.runtime.capability_status import CapabilityStatusReporter
from jarvis_v2.environment.browser_runtime import BrowserRuntime
from jarvis_v2.perception.vision import VisionService
from jarvis_v2.research.pipeline import ResearchPipeline
from jarvis_v2.code.agent import CodingAgent


def build_local_runtime(model_url: str | None = None) -> tuple[JarvisAgentRuntime, CapabilityRegistry]:
    capabilities = CapabilityRegistry().discover()

    registry = RuntimeToolRegistry(capabilities).build()
    specs = registry.specs_list()

    gateway = ModelGateway()
    gateway.register(
        ModelProfile(
            id="local-llama",
            provider="llama.cpp",
            capabilities={"planning"},
            local=True,
            available=True,
        ),
        llama_cpp_client(
            model_url or os.getenv("JARVIS_MODEL_URL", "http://127.0.0.1:8080/v1")
        ),
    )
    brain = GatewayBrainFactory(gateway).create("local-llama")

    environment = JarvisEnvironment()
    observer = EnvironmentObserver(environment.snapshot)
    fabric = JarvisKnowledgeFabric(UnifiedWorldGraph())

    # Shared security/runtime services. These are deliberately constructed
    # once so every high-impact workflow uses the same policy boundary.
    audit = AuditLog()
    policy = SecurityPolicy()
    input_gate = SensitiveInputGate()
    high_impact = HighImpactWorkflow(
        detector=SensitiveActionDetector(),
        gate=input_gate,
    )

    # Provider boundaries. Missing optional providers remain safe/unconfigured;
    # they are never represented as magically available capabilities.
    browser = BrowserRuntime()
    vision = VisionService()
    research = ResearchPipeline()

    # Device identity/session layer used by DOOM.
    device_sessions = DeviceSessionManager()
    doom_sessions = DoomSessionBridge(device_sessions)

    # Project coding orchestration is available once a project executor is
    # attached by the host application.
    coding = CodingAgent()

    # Keep these objects attached to the runtime as explicit services. This
    # gives the host application one composition root without leaking secrets
    # into the model.
    runtime = JarvisAgentRuntime(
        ActionPlanner(specs),
        registry.executor(),
        fabric,
        brain=brain,
        environment_observer=observer,
        high_impact_workflow=high_impact,
    )
    runtime.services = {
        "audit": audit,
        "policy": policy,
        "sensitive_input": input_gate,
        "high_impact": high_impact,
        "browser": browser,
        "vision": vision,
        "research": research,
        "device_sessions": device_sessions,
        "doom_sessions": doom_sessions,
        "coding": coding,
        "capabilities": CapabilityStatusReporter().report(
            browser=browser.provider,
            vision=vision.provider,
            research=research.provider,
            coding=coding.executor,
        ),
    }
    return runtime, capabilities
