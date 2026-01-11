from __future__ import annotations

import ast
from dataclasses import dataclass

from ..condition.collector import ConditionMetricsCollector
from ..function.symbol_collector import FunctionSymbolCollector
from ..if_.collector import IfCollector
from ..unit.node_collector import UnitNodeCollector
from .result import BpsResult


@dataclass
class BpsAnalyzer:
    def analyze_file(self, file_path: str) -> list[BpsResult]:
        with open(file_path, "r", encoding="utf-8") as handle:
            source = handle.read()
        tree = ast.parse(source, filename=file_path)
        unit_collector = UnitNodeCollector(file_path=file_path)
        unit_collector.visit(tree)
        results: list[BpsResult] = []
        for unit_node in unit_collector.units:
            usage = FunctionSymbolCollector().collect(unit_node.node)
            local_names = usage.locals
            if_nodes = IfCollector().collect(unit_node.node)
            if not if_nodes:
                bps = 1.0
            else:
                scores: list[float] = []
                for if_node in if_nodes:
                    metrics = ConditionMetricsCollector(local_names=local_names).collect(
                        if_node.test
                    )
                    penalty = (
                        metrics.bool_ops
                        + metrics.compare_ops
                        + 2 * metrics.calls
                        + 2 * metrics.external_refs
                    )
                    scores.append(1.0 / (1.0 + penalty))
                bps = sum(scores) / len(scores)
            results.append(BpsResult(unit=unit_node.definition, bps=bps))
        return results
