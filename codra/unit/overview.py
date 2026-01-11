from __future__ import annotations

from dataclasses import dataclass

from .definition import UnitDefinition
from .metrics import UnitMetrics


@dataclass(frozen=True)
class UnitReport:
    unit: UnitDefinition
    metrics: UnitMetrics
