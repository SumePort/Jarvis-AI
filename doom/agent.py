"""DOOM node agent: heartbeat, registration and authenticated task envelope."""
from __future__ import annotations
import threading,time
from .mesh.node import DoomNode
class DoomNodeAgent:
    def __init__(self,node:DoomNode,heartbeat_fn=None,interval=15):
        self.node=node; self.heartbeat_fn=heartbeat_fn; self.interval=interval; self._stop=threading.Event()
    def tick(self):
        self.node.heartbeat()
        if self.heartbeat_fn: return self.heartbeat_fn(self.node)
        return self.node
    def run_forever(self):
        while not self._stop.is_set():
            self.tick(); self._stop.wait(self.interval)
    def stop(self): self._stop.set()
