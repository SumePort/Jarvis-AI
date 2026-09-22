"""Build a real local JARVIS V2 runtime from installed capabilities."""
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
from jarvis_v2.actions.executor import ActionExecutor
from jarvis_v2.actions.planner import ActionPlanner


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
        llama_cpp_client(model_url or os.getenv("JARVIS_MODEL_URL", "http://127.0.0.1:8080/v1")),
    )
    brain = GatewayBrainFactory(gateway).create("local-llama")

    environment = JarvisEnvironment()
    observer = EnvironmentObserver(environment.snapshot)
    fabric = JarvisKnowledgeFabric(UnifiedWorldGraph())

    runtime = JarvisAgentRuntime(
        ActionPlanner(specs),
        registry.executor(),
        fabric,
        brain=brain,
        environment_observer=observer,
    )
    return runtime, capabilities
