"""Minimal authenticated DOOM protocol server adapter."""
from __future__ import annotations
from .protocol import Protocol,Message
class DoomProtocolServer:
    def __init__(self,key:bytes): self.key=key; self.handlers={}
    def register(self,kind,handler): self.handlers[kind]=handler
    def handle(self,wire):
        message=Protocol().decode(wire,self.key)
        handler=self.handlers.get(message.kind)
        if handler is None: raise LookupError("Unsupported DOOM message")
        return handler(message)
