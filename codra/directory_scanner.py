from __future__ import annotations

import os
from dataclasses import dataclass, field

from .python_file_scanner import PythonFileScanner
from .unit.definition import UnitDefinition


@dataclass
class DirectoryScanner:
    file_scanner: PythonFileScanner = field(default_factory=PythonFileScanner)

    def scan(self, root_path: str) -> list[UnitDefinition]:
        units: list[UnitDefinition] = []
        for current_root, dirnames, filenames in os.walk(root_path):
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                file_path = os.path.join(current_root, filename)
                units.extend(self.file_scanner.scan_file(file_path))
        return units
