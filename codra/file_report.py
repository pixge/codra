from __future__ import annotations

from dataclasses import dataclass

from .unit_report import UnitReport


@dataclass(frozen=True)
class FileReport:
    file_path: str
    units: list[UnitReport]
