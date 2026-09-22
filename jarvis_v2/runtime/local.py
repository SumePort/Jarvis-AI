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
from jarvis_v2.code.safe_executor import SafeProjectExecutor
from jarvis_v2.perception.tesseract import TesseractVisionProvider
from jarvis_v2.perception.screenshot import WindowsScreenshotProvider
from jarvis_v2.environment.playwright_session import PlaywrightSessionFactory
from jarvis_v2.environment.browser_playwright import PlaywrightBrowserProvider
from jarvis_v2.environment.screenshot_provider import ScreenshotEnvironmentProvider
from jarvis_v2.research.http_provider import HttpJsonResearchProvider
from jarvis_v2.research.background import BackgroundResearchManager
from jarvis_v2.research.browser_provider import BrowserResearchProvider
from jarvis_v2.self_improvement.engine import SelfImprovementEngine
from jarvis_v2.self_improvement.orchestrator import SelfImprovementOrchestrator
from jarvis_v2.knowledge.learning_store import LearningStore
from jarvis_v2.imagination.engine import ImaginationEngine
from jarvis_v2.imagination.experiment_log import ExperimentLog
from jarvis_v2.simulation.sandbox import MentalSandbox
from jarvis_v2.simulation.mental_model import MentalModelBuilder
from jarvis_v2.simulation.advanced import NumericalSimulator
from jarvis_v2.inventor.loop import InventorLoop
from doom.mesh.mesh import DoomMesh
from doom.provisioning import Provisioner


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
    vision = VisionService()
    if os.getenv("JARVIS_ENABLE_OCR", "0") == "1":
        try:
            vision = VisionService(TesseractVisionProvider())
        except Exception:
            pass
    if vision.provider is not None:
        try:
            environment._composite.providers.append(
                ScreenshotEnvironmentProvider(WindowsScreenshotProvider(), vision)
            )
        except Exception:
            pass
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
    research = ResearchPipeline()

    # Opt-in local providers. They are activated only when their dependencies
    # are installed and the corresponding environment flags are enabled.
    if os.getenv("JARVIS_RESEARCH_ENDPOINT"):
        try:
            research = ResearchPipeline(
                HttpJsonResearchProvider(os.environ["JARVIS_RESEARCH_ENDPOINT"])
            )
        except Exception:
            pass

    browser_session = None
    if os.getenv("JARVIS_ENABLE_PLAYWRIGHT", "0") == "1":
        try:
            browser_session = PlaywrightSessionFactory(
                headless=os.getenv("JARVIS_BROWSER_HEADLESS", "0") == "1"
            )
            page = browser_session.start()
            browser = BrowserRuntime(PlaywrightBrowserProvider(page))
        except Exception:
            browser_session = None

    coding = CodingAgent(SafeProjectExecutor())
    if browser.provider is not None and os.getenv("JARVIS_ENABLE_BROWSER_RESEARCH", "0") == "1":
        research = ResearchPipeline(BrowserResearchProvider(browser))
    learning_store = LearningStore()
    background_research = BackgroundResearchManager(
        research,
        summarizer=lambda result: gateway.complete(
            "local-llama",
            "[JARVIS_RAW]\nSynthesize this research into a concise, evidence-grounded summary. "
            "Do not invent facts. Preserve uncertainty and cite source URLs.\n"
            + result.synthesis_context[:18000],
        ),
        learning_store=learning_store,
    )
    project_root = os.getenv("JARVIS_PROJECT_ROOT", os.getcwd())
    self_improvement = SelfImprovementEngine(project_root, SafeProjectExecutor())
    self_improvement_orchestrator = SelfImprovementOrchestrator(
        self_improvement,
        brain=brain,
        text_model=lambda prompt: gateway.complete("local-llama", prompt),
        research=research,
        learning_store=learning_store,
    )
    imagination = ImaginationEngine(
        text_model=lambda prompt: gateway.complete("local-llama", prompt)
    )
    experiment_log = ExperimentLog()
    mental_sandbox = MentalSandbox()
    mental_model_builder = MentalModelBuilder(
        text_model=lambda prompt: gateway.complete("local-llama", prompt)
    )
    numerical_simulator = NumericalSimulator()
    inventor_loop = InventorLoop(
        imagination=imagination,
        sandbox=mental_sandbox,
        model_builder=mental_model_builder,
    )
    doom_mesh = DoomMesh()
    provisioner = Provisioner()

    # Device identity/session layer used by DOOM.
    device_sessions = DeviceSessionManager()
    doom_sessions = DoomSessionBridge(device_sessions)

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
        "background_research": background_research,
        "device_sessions": device_sessions,
        "doom_sessions": doom_sessions,
        "coding": coding,
        "self_improvement": self_improvement,
        "self_improvement_orchestrator": self_improvement_orchestrator,
        "learning_store": learning_store,
        "imagination": imagination,
        "experiment_log": experiment_log,
        "mental_sandbox": mental_sandbox,
        "mental_model_builder": mental_model_builder,
        "numerical_simulator": numerical_simulator,
        "inventor_loop": inventor_loop,
        "doom_mesh": doom_mesh,
        "provisioner": provisioner,
        "browser_session": browser_session,
        "capabilities": CapabilityStatusReporter().report(
            browser=browser.provider,
            vision=vision.provider,
            research=research.provider,
            coding=coding.executor,
        ),
    }
    return runtime, capabilities
