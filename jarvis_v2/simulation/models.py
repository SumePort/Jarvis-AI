"""Provider-neutral mental sandbox contracts."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Parameter:
    name: str
    value: float
    minimum: float | None = None
    maximum: float | None = None
    unit: str = ""

@dataclass(frozen=True)
class SimulationSpec:
    name: str
    objective: str
    parameters: tuple[Parameter,...]
    equations: tuple[str,...] = ()
    assumptions: tuple[str,...] = ()
    constraints: tuple[str,...] = ()

@dataclass(frozen=True)
class SimulationOutcome:
    status: str
    values: dict[str,float]
    violated_constraints: tuple[str,...] = ()
    notes: tuple[str,...] = ()

@dataclass
class SimulationRun:
    spec: SimulationSpec
    outcomes: list[SimulationOutcome] = field(default_factory=list)
    sensitivity: dict[str,float] = field(default_factory=dict)
    conclusion: str = ""
