from __future__ import annotations

import ast
from dataclasses import dataclass

from ..condition.collector import ConditionMetricsCollector
from ..function.symbol_collector import FunctionSymbolCollector
from ..if_.collector import IfCollector
from ..unit.node import UnitNode
from ..unit.node_collector import UnitNodeCollector
from .result import BpsResult


@dataclass
class BpsAnalyzer:
    def analyze_file(self, file_path: str) -> list[BpsResult]:
        tree = self._parse_file(file_path)
        unit_nodes = self._collect_units(tree, file_path)
        scores = [self._collect_bps(unit_node) for unit_node in unit_nodes]
        return self._build_results(unit_nodes, scores)

    def _parse_file(self, file_path: str) -> ast.AST:
        with open(file_path, "r", encoding="utf-8") as handle:
            source = handle.read()
        return ast.parse(source, filename=file_path)

    def _collect_units(self, tree: ast.AST, file_path: str) -> list[UnitNode]:
        unit_collector = UnitNodeCollector(file_path=file_path)
        unit_collector.visit(tree)
        return unit_collector.units

    def _collect_bps(self, unit_node: UnitNode) -> float:
        usage = FunctionSymbolCollector().collect(unit_node.node)
        local_names = usage.locals
        if_nodes = IfCollector().collect(unit_node.node)
        if not if_nodes:
            return 1.0
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
        return sum(scores) / len(scores)

    def _build_results(
        self, unit_nodes: list[UnitNode], scores: list[float]
    ) -> list[BpsResult]:
        return [
            BpsResult(unit=unit_node.definition, bps=bps)
            for unit_node, bps in zip(unit_nodes, scores, strict=True)
        ]
