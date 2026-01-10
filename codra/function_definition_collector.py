from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass
class FunctionDefinitionCollector(ast.NodeVisitor):
    names: set[str] = field(default_factory=set)
    class_stack: list[str] = field(default_factory=list)

    def collect(self, tree: ast.AST) -> set[str]:
        self.visit(tree)
        return set(self.names)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        for statement in node.body:
            self.visit(statement)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if not self.class_stack:
            self.names.add(node.name)
        for statement in node.body:
            self.visit(statement)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if not self.class_stack:
            self.names.add(node.name)
        for statement in node.body:
            self.visit(statement)
