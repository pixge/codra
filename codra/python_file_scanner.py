from __future__ import annotations

import ast
from dataclasses import dataclass

from .function_extractor import FunctionExtractor
from .unit.definition import UnitDefinition


@dataclass
class PythonFileScanner:
    def scan_file(self, file_path: str) -> list[UnitDefinition]:
        with open(file_path, "r", encoding="utf-8") as handle:
            source = handle.read()
        tree = ast.parse(source, filename=file_path)
        extractor = FunctionExtractor(file_path=file_path)
        extractor.visit(tree)
        return extractor.units
