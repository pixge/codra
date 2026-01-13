from __future__ import annotations

import ast
from ast import NodeVisitor
from dataclasses import dataclass, field


@dataclass
class IfCollector(NodeVisitor):
    """AST visitor collecting if statements via NodeVisitor."""
    nodes: list[ast.If] = field(default_factory=list)

    def collect(self, node: ast.AST) -> list[ast.If]:
        for statement in node.body:
            super().visit(statement)
        return list(self.nodes)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return None

    def visit_If(self, node: ast.If) -> None:
        self.nodes.append(node)
        super().generic_visit(node)
