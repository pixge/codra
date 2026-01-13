from __future__ import annotations

from dataclasses import dataclass

from .file import FileReport
from .summary import ReportSummary


@dataclass(frozen=True)
class Report:
    schema_version: str
    language: str
    summary: ReportSummary
    files: list[FileReport]
