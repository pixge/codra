from __future__ import annotations

from dataclasses import dataclass

from .unit.definition import UnitDefinition


@dataclass(frozen=True)
class CsaResult:
    unit: UnitDefinition
    csa_main: int
    external_symbols: list[str]
    self_fields_read: list[str]
