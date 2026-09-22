from dataclasses import dataclass
@dataclass
class InventionCycle:
    idea:str
    research:str=""
    imagination:object=None
    simulations:list=None
    experiments:list=None
    observations:list=None
    def __post_init__(self):
        self.simulations=self.simulations or []; self.experiments=self.experiments or []; self.observations=self.observations or []
class InventorLoop:
    def __init__(self,imagination,research=None,sandbox=None,model_builder=None):
        self.imagination=imagination; self.research=research; self.sandbox=sandbox; self.model_builder=model_builder
    def think(self,idea,context=""):
        research_text=""
        cycle=InventionCycle(idea,research_text)
        cycle.imagination=self.imagination.explore(idea,context,research_text)
        if self.model_builder and self.sandbox:
            for spec in self.model_builder.build(cycle.imagination): cycle.simulations.append(self.sandbox.run(spec))
        return cycle
