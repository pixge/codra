from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnitKey:
    file_path: str
    qualified_id: str
    kind: str
    start_line: int
    end_line: int
