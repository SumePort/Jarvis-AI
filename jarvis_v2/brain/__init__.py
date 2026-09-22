"""Provider-neutral JARVIS V2 brain contracts."""
from .provider import BrainProvider, BrainResponse
from .json_brain import JsonBrainAdapter
__all__ = ["BrainProvider", "BrainResponse", "JsonBrainAdapter"]
