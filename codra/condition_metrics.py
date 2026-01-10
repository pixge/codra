from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConditionMetrics:
    bool_ops: int
    compare_ops: int
    calls: int
    external_refs: int
