from __future__ import annotations

from dataclasses import dataclass

from .file_report import FileReport
from .report_summary import ReportSummary


@dataclass(frozen=True)
class Report:
    schema_version: str
    language: str
    summary: ReportSummary
    files: list[FileReport]
