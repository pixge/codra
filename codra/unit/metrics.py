from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnitMetrics:
    csa_main: int
    external_symbols: list[str]
    self_fields_read: list[str]
    id_max: int
    id_avg: float
    unresolved_calls: list[str]
    bps: float
