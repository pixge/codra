from __future__ import annotations

from dataclasses import dataclass

from .report.builder import ReportBuilder
from .report.serializer import ReportSerializer


@dataclass(frozen=True)
class CliDependencies:
    builder: ReportBuilder
    serializer: ReportSerializer
