from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportSummary:
    total_files: int
    total_units: int
