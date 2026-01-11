from dataclasses import dataclass


@dataclass(frozen=True)
class UnitDefinition:
    file_path: str
    qualified_id: str
    kind: str
    start_line: int
    end_line: int
