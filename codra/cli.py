from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from .bps_analyzer import BpsAnalyzer
from .csa_analyzer import CsaAnalyzer
from .file_path_collector import FilePathCollector
from .indirection_analyzer import IndirectionAnalyzer
from .report_builder import ReportBuilder
from .report_serializer import ReportSerializer
from .threshold_config import ThresholdConfig


@dataclass
class Cli:
    def run(self, args: list[str]) -> int:
        parser = argparse.ArgumentParser()
        parser.add_argument("path")
        parser.add_argument("--threshold-csa", type=int, default=None)
        parser.add_argument("--threshold-id", type=int, default=None)
        parser.add_argument("--threshold-bps", type=float, default=None)
        options = parser.parse_args(args)
        thresholds = ThresholdConfig(
            csa=options.threshold_csa,
            indirection=options.threshold_id,
            bps=options.threshold_bps,
        )
        builder = ReportBuilder(
            csa_analyzer=CsaAnalyzer(),
            indirection_analyzer=IndirectionAnalyzer(),
            bps_analyzer=BpsAnalyzer(),
            path_collector=FilePathCollector(),
        )
        report = builder.build(options.path)
        serializer = ReportSerializer()
        output = serializer.to_json(report)
        sys.stdout.write(output)
        sys.stdout.write("\n")
        return 0 if builder.check_thresholds(report, thresholds) else 1


def main() -> None:
    raise SystemExit(Cli().run(sys.argv[1:]))
