from __future__ import annotations

import ast
from ast import NodeVisitor
from dataclasses import dataclass, field


@dataclass
class AliasCollector(NodeVisitor):
    """AST visitor collecting top-level alias assignments via NodeVisitor."""
    aliases: dict[str, str] = field(default_factory=dict)
    depth: int = 0

    def collect(self, tree: ast.AST) -> dict[str, str]:
        super().visit(tree)
        return dict(self.aliases)

    def visit_Module(self, node: ast.Module) -> None:
        self.depth += 1
        for statement in node.body:
            super().visit(statement)
        self.depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return None

    def visit_Assign(self, node: ast.Assign) -> None:
        if self.depth != 1:
            return
        if not isinstance(node.value, ast.Name):
            return
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.aliases[target.id] = node.value.id

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self.depth != 1:
            return
        if not isinstance(node.target, ast.Name):
            return
        if not isinstance(node.value, ast.Name):
            return
        self.aliases[node.target.id] = node.value.id
