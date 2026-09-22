"""Optional infrastructure adapters. They require explicit credentials/configuration."""
from __future__ import annotations
class CallableProvisioner:
    def __init__(self,name,provision_fn): self.name=name; self._fn=provision_fn
    def provision(self,request): return self._fn(request)
class NoopProvisioner:
    name="unconfigured"
    def provision(self,request): raise RuntimeError("Infrastructure provider is not configured")
