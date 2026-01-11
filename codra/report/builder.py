from __future__ import annotations

import logging
from dataclasses import dataclass

from ..bps_analyzer import BpsAnalyzer
from ..csa_analyzer import CsaAnalyzer
from ..file_path_collector import FilePathCollector
from ..indirection_analyzer import IndirectionAnalyzer
from ..threshold_config import ThresholdConfig
from ..unit.definition import UnitDefinition
from ..unit.key import UnitKey
from ..unit.metrics import UnitMetrics
from ..unit.overview import UnitReport
from .file import FileReport
from .model import Report
from .summary import ReportSummary


logger = logging.getLogger(__name__)


@dataclass
class ReportBuilder:
    csa_analyzer: CsaAnalyzer
    indirection_analyzer: IndirectionAnalyzer
    bps_analyzer: BpsAnalyzer
    path_collector: FilePathCollector

    def build(self, root_path: str) -> Report:
        logger.info("Collecting files from %s", root_path)
        file_paths = self.path_collector.collect(root_path)
        files: list[FileReport] = []
        total_units = 0
        for file_path in file_paths:
            logger.info("Analyzing %s", file_path)
            csa_results = self.csa_analyzer.analyze_file(file_path)
            indirection_results = self.indirection_analyzer.analyze_file(file_path)
            bps_results = self.bps_analyzer.analyze_file(file_path)
            csa_map = {self._key(result.unit): result for result in csa_results}
            indirection_map = {
                self._key(result.unit): result for result in indirection_results
            }
            bps_map = {self._key(result.unit): result for result in bps_results}
            keys = sorted(
                {**csa_map, **indirection_map, **bps_map}.keys(),
                key=self._sort_key,
            )
            units: list[UnitReport] = []
            for key in keys:
                unit = self._resolve_unit(key, csa_map, indirection_map, bps_map)
                metrics = self._resolve_metrics(key, csa_map, indirection_map, bps_map)
                units.append(UnitReport(unit=unit, metrics=metrics))
            files.append(FileReport(file_path=file_path, units=units))
            total_units += len(units)
        summary = ReportSummary(total_files=len(files), total_units=total_units)
        return Report(
            schema_version="1.0",
            language="python",
            summary=summary,
            files=files,
        )

    def check_thresholds(self, report: Report, thresholds: ThresholdConfig) -> bool:
        for file_report in report.files:
            for unit in file_report.units:
                metrics = unit.metrics
                if thresholds.csa is not None and metrics.csa_main > thresholds.csa:
                    return False
                if (
                    thresholds.indirection is not None
                    and metrics.id_max > thresholds.indirection
                ):
                    return False
                if thresholds.bps is not None and metrics.bps < thresholds.bps:
                    return False
        return True

    def _key(self, unit: UnitDefinition) -> UnitKey:
        return UnitKey(
            file_path=unit.file_path,
            qualified_id=unit.qualified_id,
            kind=unit.kind,
            start_line=unit.start_line,
            end_line=unit.end_line,
        )

    def _sort_key(self, key: UnitKey) -> tuple[str, int, int, str]:
        return (key.qualified_id, key.start_line, key.end_line, key.kind)

    def _resolve_unit(
        self,
        key: UnitKey,
        csa_map: dict[UnitKey, object],
        indirection_map: dict[UnitKey, object],
        bps_map: dict[UnitKey, object],
    ) -> UnitDefinition:
        for mapping in (csa_map, indirection_map, bps_map):
            if key in mapping:
                return mapping[key].unit
        return UnitDefinition(
            file_path=key.file_path,
            qualified_id=key.qualified_id,
            kind=key.kind,
            start_line=key.start_line,
            end_line=key.end_line,
        )

    def _resolve_metrics(
        self,
        key: UnitKey,
        csa_map: dict[UnitKey, object],
        indirection_map: dict[UnitKey, object],
        bps_map: dict[UnitKey, object],
    ) -> UnitMetrics:
        csa_result = csa_map.get(key)
        indirection_result = indirection_map.get(key)
        bps_result = bps_map.get(key)
        return UnitMetrics(
            csa_main=csa_result.csa_main if csa_result else 0,
            external_symbols=csa_result.external_symbols if csa_result else [],
            self_fields_read=csa_result.self_fields_read if csa_result else [],
            id_max=indirection_result.id_max if indirection_result else 0,
            id_avg=indirection_result.id_avg if indirection_result else 0.0,
            unresolved_calls=(
                indirection_result.unresolved_calls if indirection_result else []
            ),
            bps=bps_result.bps if bps_result else 1.0,
        )
