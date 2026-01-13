from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CliArgs:
    path: str
    threshold_csa: int | None
    threshold_id: int | None
    threshold_bps: float | None
    log_level: str
    output: str | None
