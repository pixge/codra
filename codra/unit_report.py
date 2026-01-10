from __future__ import annotations

from dataclasses import dataclass

from .unit_definition import UnitDefinition
from .unit_metrics import UnitMetrics


@dataclass(frozen=True)
class UnitReport:
    unit: UnitDefinition
    metrics: UnitMetrics
