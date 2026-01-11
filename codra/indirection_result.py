from __future__ import annotations

from dataclasses import dataclass

from .unit.definition import UnitDefinition


@dataclass(frozen=True)
class IndirectionResult:
    unit: UnitDefinition
    id_max: int
    id_avg: float
    unresolved_calls: list[str]
