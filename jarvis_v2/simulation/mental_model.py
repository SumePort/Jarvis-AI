"""Build simulation candidates from imagination hypotheses."""
from __future__ import annotations
import json
from .models import SimulationSpec, Parameter
from jarvis_v2.imagination.models import ImaginationResult

class MentalModelBuilder:
    def __init__(self,text_model=None): self.text_model=text_model
    def build(self,idea:ImaginationResult)->list[SimulationSpec]:
        if not self.text_model:return []
        prompt="""Convert the following engineering hypotheses into small, transparent simulation models.
Only use scalar numeric parameters and algebraic equations/boolean constraints.
Do not claim simulation proves physical reality.
Return JSON: {"models":[{"name":"","objective":"","parameters":[{"name":"","value":0,"minimum":0,"maximum":1,"unit":""}],"equations":["output=x*y"],"assumptions":[],"constraints":["output>=0"]}]}.
Hypotheses:
"""+json.dumps([h.__dict__ | {"level":h.level.value} for h in idea.hypotheses])
        data=json.loads(self.text_model("[JARVIS_RAW_JSON]\n"+prompt))
        out=[]
        for m in data.get("models",[]):
            ps=tuple(Parameter(str(p["name"]),float(p["value"]),
                               float(p["minimum"]) if p.get("minimum") is not None else None,
                               float(p["maximum"]) if p.get("maximum") is not None else None,
                               str(p.get("unit",""))) for p in m.get("parameters",[]))
            out.append(SimulationSpec(str(m.get("name","model")),str(m.get("objective","")),
                                      ps,tuple(map(str,m.get("equations",[]))),
                                      tuple(map(str,m.get("assumptions",[]))),
                                      tuple(map(str,m.get("constraints",[])))))
        return out
