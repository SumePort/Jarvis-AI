from .node import DoomNode,NodeState
class DoomMesh:
    def __init__(self): self.nodes={}
    def register(self,node): self.nodes[node.node_id]=node; return node
    def heartbeat(self,node_id): self.nodes[node_id].heartbeat(); return self.nodes[node_id]
    def available(self,capability=None):
        nodes=[n for n in self.nodes.values() if n.state==NodeState.ONLINE]
        return [n for n in nodes if capability is None or capability in n.capabilities]
    def choose(self,capability):
        candidates=self.available(capability)
        if not candidates: raise LookupError("No DOOM node provides capability")
        return max(candidates,key=lambda n:n.resources.get("free",0))
