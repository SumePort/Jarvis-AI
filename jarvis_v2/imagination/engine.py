"""Human-style possibility exploration without treating speculation as fact."""
from __future__ import annotations
from dataclasses import dataclass
import json
import uuid
from .models import PossibilityLevel, Hypothesis, Analogy, Experiment, ImaginationResult

class ImaginationEngine:
    """Turns an idea into hypotheses, analogies and testable experiments.

    The engine deliberately separates what is known from what is imagined.
    A language model may supply candidates, but this layer owns the contracts,
    classification and experiment structure.
    """

    def __init__(self, text_model=None):
        self.text_model = text_model

    def explore(self, goal: str, context: str = "", research: str = "") -> ImaginationResult:
        if self.text_model is None:
            return self._baseline(goal)
        prompt = f"""Explore this engineering idea as a human inventor.
Do NOT answer merely 'impossible' because it is novel.
Distinguish facts from hypotheses. Treat unknown as unknown.
Use these levels exactly: proven, engineeringally_feasible, plausible,
speculative, experimentally_unknown, constrained, currently_infeasible,
physically_contradictory.
Return ONLY JSON:
{{"known":[],"constraints":[],"hypotheses":[{{"statement":"","mechanism":"","level":"","evidence":[],"uncertainties":[]}}],
"analogies":[{{"source_domain":"","source_mechanism":"","target_domain":"","transfer_reason":"","limitations":[]}}],
"experiments":[{{"objective":"","hypothesis_id":"","materials":[],"procedure":[],"expected_observation":"","safety_notes":[],"success_criteria":[]}}],
"conclusion":""}}
Goal: {goal}
Context: {context[:8000]}
Research: {research[:12000]}"""
        raw = self.text_model("[JARVIS_RAW_JSON]\n" + prompt)
        data = json.loads(raw)
        hypotheses=[]
        for item in data.get("hypotheses", []):
            level=PossibilityLevel(item.get("level","experimentally_unknown"))
            hypotheses.append(Hypothesis(
                "hyp_" + uuid.uuid4().hex[:10], item.get("statement",""),
                item.get("mechanism",""), level,
                tuple(item.get("evidence",[])), tuple(item.get("uncertainties",[]))
            ))
        id_map=[h.id for h in hypotheses]
        experiments=[]
        for item in data.get("experiments", []):
            hid=item.get("hypothesis_id")
            if not hid or hid not in id_map:
                hid=id_map[0] if id_map else ""
            experiments.append(Experiment(
                "exp_" + uuid.uuid4().hex[:10], item.get("objective",""), hid,
                tuple(item.get("materials",[])), tuple(item.get("procedure",[])),
                item.get("expected_observation",""),
                tuple(item.get("safety_notes",[])), tuple(item.get("success_criteria",[]))
            ))
        analogies=[Analogy(
            str(x.get("source_domain","")), str(x.get("source_mechanism","")),
            str(x.get("target_domain","")), str(x.get("transfer_reason","")),
            tuple(x.get("limitations",[]))
        ) for x in data.get("analogies", [])]
        return ImaginationResult(
            goal, tuple(data.get("known",[])), tuple(data.get("constraints",[])),
            hypotheses, analogies, experiments, str(data.get("conclusion",""))
        )

    def _baseline(self, goal: str) -> ImaginationResult:
        h=Hypothesis("hyp_baseline","The requested mechanism may be achievable through an alternative mechanism.",
                     "Decompose the goal into observable functions and substitute available technologies.",
                     PossibilityLevel.EXPERIMENTALLY_UNKNOWN,
                     uncertainties=("No research/model evidence supplied.",))
        return ImaginationResult(goal,hypotheses=[h],conclusion="Unknown is not the same as impossible; an experiment is required.")
