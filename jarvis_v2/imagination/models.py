"""Data contracts for imaginative and experimental reasoning."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

class PossibilityLevel(str, Enum):
    PROVEN = "proven"
    ENGINEERINGALLY_FEASIBLE = "engineeringally_feasible"
    PLAUSIBLE = "plausible"
    SPECULATIVE = "speculative"
    EXPERIMENTALLY_UNKNOWN = "experimentally_unknown"
    CONSTRAINED = "constrained"
    CURRENTLY_INFEASIBLE = "currently_infeasible"
    PHYSICALLY_CONTRADICTORY = "physically_contradictory"

@dataclass(frozen=True)
class Hypothesis:
    id: str
    statement: str
    mechanism: str
    level: PossibilityLevel
    evidence: tuple[str,...] = ()
    uncertainties: tuple[str,...] = ()

@dataclass(frozen=True)
class Analogy:
    source_domain: str
    source_mechanism: str
    target_domain: str
    transfer_reason: str
    limitations: tuple[str,...] = ()

@dataclass(frozen=True)
class Experiment:
    id: str
    objective: str
    hypothesis_id: str
    materials: tuple[str,...]
    procedure: tuple[str,...]
    expected_observation: str
    safety_notes: tuple[str,...] = ()
    success_criteria: tuple[str,...] = ()

@dataclass
class ImaginationResult:
    goal: str
    known: tuple[str,...] = ()
    constraints: tuple[str,...] = ()
    hypotheses: list[Hypothesis] = field(default_factory=list)
    analogies: list[Analogy] = field(default_factory=list)
    experiments: list[Experiment] = field(default_factory=list)
    conclusion: str = ""
