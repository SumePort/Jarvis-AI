from dataclasses import dataclass,field
@dataclass(frozen=True)
class Percept:
    kind:str
    label:str
    confidence:float
    source:str
    bbox:tuple[float,float,float,float]|None=None
    attributes:dict[str,str]=field(default_factory=dict)
@dataclass
class WorldState:
    percepts:list[Percept]=field(default_factory=list)
    timestamp:float=0.0
    def high_confidence(self,threshold=.7): return [p for p in self.percepts if p.confidence>=threshold]
