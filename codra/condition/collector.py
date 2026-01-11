from __future__ import annotations

import ast
from ast import NodeVisitor
from dataclasses import dataclass

from .metrics import ConditionMetrics


@dataclass
class ConditionMetricsCollector(NodeVisitor):
    """AST visitor collecting condition metrics via NodeVisitor."""
    local_names: set[str]
    bool_ops: int = 0
    compare_ops: int = 0
    calls: int = 0
    external_refs: int = 0

    def collect(self, node: ast.AST) -> ConditionMetrics:
        super().visit(node)
        return ConditionMetrics(
            bool_ops=self.bool_ops,
            compare_ops=self.compare_ops,
            calls=self.calls,
            external_refs=self.external_refs,
        )

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.bool_ops += max(0, len(node.values) - 1)
        super().generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        self.compare_ops += len(node.ops)
        super().generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        self.calls += 1
        super().generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load) and node.id not in self.local_names:
            self.external_refs += 1
