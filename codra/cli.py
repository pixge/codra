from __future__ import annotations

import argparse
import logging
import sys

from .bps_analyzer import BpsAnalyzer
from .csa_analyzer import CsaAnalyzer
from .cli_args import CliArgs
from .cli_dependencies import CliDependencies
from .file_path_collector import FilePathCollector
from .indirection_analyzer import IndirectionAnalyzer
from .report.builder import ReportBuilder
from .report.serializer import ReportSerializer
from .threshold_config import ThresholdConfig


logger = logging.getLogger(__name__)


def parse_args(argv: list[str]) -> CliArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--threshold-csa", type=int, default=None)
    parser.add_argument("--threshold-id", type=int, default=None)
    parser.add_argument("--threshold-bps", type=float, default=None)
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (e.g. DEBUG, INFO, WARNING).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path. Defaults to stdout when omitted.",
    )
    o = parser.parse_args(argv)
    return CliArgs(
        path=o.path,
        threshold_csa=o.threshold_csa,
        threshold_id=o.threshold_id,
        threshold_bps=o.threshold_bps,
        log_level=o.log_level,
        output=o.output,
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


def configure_logging(log_level: str) -> None:
    level = logging._nameToLevel.get(log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(levelname)s:%(name)s:%(message)s",
    )


def run_cli(args: CliArgs, deps: CliDependencies) -> int:
    logger.info("Starting analysis for %s", args.path)
    report = deps.builder.build(args.path)
    payload = deps.serializer.to_json(report)
    if args.output:
        logger.info("Writing report to %s", args.output)
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.write("\n")
    else:
        logger.info("Writing report to stdout")
        sys.stdout.write(payload)
        sys.stdout.write("\n")
    return 0 if deps.builder.check_thresholds(report, build_thresholds(args)) else 1


def main() -> None:
    args = parse_args(sys.argv[1:])
    configure_logging(args.log_level)
    raise SystemExit(run_cli(args, build_dependencies()))


if __name__ == "__main__":
    main()
