from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass

from .report import Report


@dataclass
class ReportSerializer:
    def to_json(self, report: Report) -> str:
        return json.dumps(asdict(report), sort_keys=True)
