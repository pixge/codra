from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class FilePathCollector:
    def collect(self, root_path: str) -> list[str]:
        paths: list[str] = []
        for current_root, dirnames, filenames in os.walk(root_path):
            dirnames.sort()
            filenames.sort()
            for filename in filenames:
                if filename.endswith(".py"):
                    paths.append(os.path.join(current_root, filename))
        return paths
