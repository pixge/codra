from __future__ import annotations

import ast
from ast import NodeVisitor
from dataclasses import dataclass, field


@dataclass
class CallCollector(NodeVisitor):
    """AST visitor collecting call expressions via NodeVisitor."""
    calls: list[str] = field(default_factory=list)

    def collect(self, node: ast.AST) -> list[str]:
        for statement in node.body:
            super().visit(statement)
        return list(self.calls)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return None

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "self":
                self.calls.append(f"self.{node.func.attr}")
        super().generic_visit(node)
