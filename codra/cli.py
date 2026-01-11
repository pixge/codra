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


@dataclass(frozen=True)
class CliArgs:
    path: str
    threshold_csa: int | None
    threshold_id: int | None
    threshold_bps: float | None


@dataclass(frozen=True)
class CliDependencies:
    builder: ReportBuilder
    serializer: ReportSerializer


def parse_args(argv: list[str]) -> CliArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--threshold-csa", type=int, default=None)
    parser.add_argument("--threshold-id", type=int, default=None)
    parser.add_argument("--threshold-bps", type=float, default=None)
    o = parser.parse_args(argv)
    return CliArgs(
        path=o.path,
        threshold_csa=o.threshold_csa,
        threshold_id=o.threshold_id,
        threshold_bps=o.threshold_bps,
    )


def build_thresholds(args: CliArgs) -> ThresholdConfig:
    return ThresholdConfig(
        csa=args.threshold_csa,
        indirection=args.threshold_id,
        bps=args.threshold_bps,
    )


def build_dependencies() -> CliDependencies:
    builder = ReportBuilder(
        csa_analyzer=CsaAnalyzer(),
        indirection_analyzer=IndirectionAnalyzer(),
        bps_analyzer=BpsAnalyzer(),
        path_collector=FilePathCollector(),
    )
    return CliDependencies(builder=builder, serializer=ReportSerializer())


def run_cli(args: CliArgs, deps: CliDependencies) -> int:
    report = deps.builder.build(args.path)
    sys.stdout.write(deps.serializer.to_json(report))
    sys.stdout.write("\n")
    return 0 if deps.builder.check_thresholds(report, build_thresholds(args)) else 1


def main() -> None:
    raise SystemExit(run_cli(parse_args(sys.argv[1:]), build_dependencies()))


if __name__ == "__main__":
    main()
