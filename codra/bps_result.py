from __future__ import annotations

from dataclasses import dataclass

from .unit_definition import UnitDefinition


@dataclass(frozen=True)
class BpsResult:
    unit: UnitDefinition
    bps: float
