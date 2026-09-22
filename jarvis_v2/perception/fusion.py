from .world import WorldState
class PerceptionFusion:
    def fuse(self,observations):
        best={}
        for p in observations:
            key=(p.kind,p.label)
            if key not in best or p.confidence>best[key].confidence: best[key]=p
        return WorldState(list(best.values()))
