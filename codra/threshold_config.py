from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThresholdConfig:
    csa: int | None
    indirection: int | None
    bps: float | None
