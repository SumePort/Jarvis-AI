from dataclasses import dataclass,field
from enum import Enum
import time,uuid
class NodeState(str,Enum): ONLINE="online"; OFFLINE="offline"; DRAINING="draining"
@dataclass
class DoomNode:
    node_id:str=field(default_factory=lambda:"node_"+uuid.uuid4().hex[:12])
    device_id:str=""
    capabilities:set[str]=field(default_factory=set)
    resources:dict[str,float]=field(default_factory=dict)
    state:NodeState=NodeState.ONLINE
    last_heartbeat:float=field(default_factory=time.time)
    def heartbeat(self): self.last_heartbeat=time.time(); self.state=NodeState.ONLINE
