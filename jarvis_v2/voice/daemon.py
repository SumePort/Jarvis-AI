"""Always-on voice host."""
from __future__ import annotations
import threading,time
class VoiceDaemon:
    def __init__(self,agent,stop_event=None):
        self.agent=agent; self.stop_event=stop_event or threading.Event()
    def run_forever(self,interval=.05):
        while not self.stop_event.is_set():
            self.agent.run_once()
            if interval: time.sleep(interval)
    def stop(self): self.stop_event.set()
