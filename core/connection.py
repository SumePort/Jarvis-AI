"""Cached internet connectivity state for hybrid routing.

The local core never depends on this module being online. Connectivity checks are
best-effort and cached so normal local commands do not repeatedly hit the network.
"""
from __future__ import annotations

import socket
import time
from dataclasses import dataclass


@dataclass
class ConnectionState:
    online: bool = False
    checked_at: float = 0.0
    ttl_seconds: float = 15.0


class ConnectionManager:
    def __init__(self, host: str = "1.1.1.1", port: int = 53, timeout: float = 1.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.state = ConnectionState()

    def is_online(self, force: bool = False) -> bool:
        now = time.monotonic()
        if not force and now - self.state.checked_at < self.state.ttl_seconds:
            return self.state.online
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout):
                self.state.online = True
        except OSError:
            self.state.online = False
        self.state.checked_at = now
        return self.state.online
