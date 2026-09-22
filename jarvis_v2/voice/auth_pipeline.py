from enum import Enum
class VoiceState(str,Enum):
    SLEEPING="sleeping"; WAKING="waking"; AUTHENTICATING="authenticating"; ACTIVE="active"; LOGGED_OUT="logged_out"
class VoiceSessionPipeline:
    def __init__(self,agent): self.agent=agent; self.state=VoiceState.SLEEPING
    def tick(self):
        result=self.agent.run_once()
        if result.status=="handled": self.state=VoiceState.ACTIVE
        elif result.status=="sleeping": self.state=VoiceState.SLEEPING
        return result
