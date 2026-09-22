"""Create a Brain adapter from the model gateway."""
from __future__ import annotations
from jarvis_v2.brain import JsonBrainAdapter
from .gateway import ModelGateway

class GatewayBrainFactory:
    def __init__(self, gateway: ModelGateway) -> None:
        self.gateway=gateway

    def create(self, model_id: str) -> JsonBrainAdapter:
        return JsonBrainAdapter(lambda prompt: self.gateway.complete(model_id, prompt))
