from __future__ import annotations

from dataclasses import dataclass

from .unit.definition import UnitDefinition


@dataclass(frozen=True)
class BpsResult:
    unit: UnitDefinition
    bps: float
