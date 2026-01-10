from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass
class ModuleSymbolCollector(ast.NodeVisitor):
    symbols: set[str] = field(default_factory=set)

    def collect(self, tree: ast.AST) -> set[str]:
        self.visit(tree)
        return set(self.symbols)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.symbols.add(node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.symbols.add(node.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.symbols.add(node.name)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname or alias.name.split(".", 1)[0]
            self.symbols.add(name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            name = alias.asname or alias.name
            self.symbols.add(name)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self.symbols.update(self._extract_target_names(target))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.symbols.update(self._extract_target_names(node.target))
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.symbols.update(self._extract_target_names(node.target))
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.symbols.update(self._extract_target_names(node.target))
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.symbols.update(self._extract_target_names(node.target))
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if item.optional_vars is not None:
                self.symbols.update(self._extract_target_names(item.optional_vars))
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        for item in node.items:
            if item.optional_vars is not None:
                self.symbols.update(self._extract_target_names(item.optional_vars))
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if isinstance(node.name, str):
            self.symbols.add(node.name)
        elif node.name is not None:
            self.symbols.update(self._extract_target_names(node.name))
        self.generic_visit(node)

    def _extract_target_names(self, node: ast.AST) -> set[str]:
        names: set[str] = set()
        for target in ast.walk(node):
            if isinstance(target, ast.Name):
                names.add(target.id)
        return names
