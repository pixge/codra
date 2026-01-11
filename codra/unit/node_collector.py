from __future__ import annotations

import ast
from dataclasses import dataclass, field

from .definition import UnitDefinition
from .node import UnitNode


@dataclass
class UnitNodeCollector(ast.NodeVisitor):
    file_path: str
    units: list[UnitNode] = field(default_factory=list)
    class_stack: list[str] = field(default_factory=list)
    function_stack: list[str] = field(default_factory=list)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_function(node)

    def _handle_function(self, node: ast.AST) -> None:
        name = node.name
        is_direct_method = bool(self.class_stack) and not self.function_stack
        if is_direct_method:
            qualified_id = f"{self.class_stack[-1]}.{name}"
            kind = "method"
        else:
            parts = []
            if self.class_stack:
                parts.append(self.class_stack[-1])
            if self.function_stack:
                parts.extend(self.function_stack)
            parts.append(name)
            qualified_id = ".".join(parts)
            kind = "function"
        start_line = getattr(node, "lineno", 0) or 0
        end_line = getattr(node, "end_lineno", 0) or start_line
        definition = UnitDefinition(
            file_path=self.file_path,
            qualified_id=qualified_id,
            kind=kind,
            start_line=start_line,
            end_line=end_line,
        )
        self.units.append(UnitNode(definition=definition, node=node))
        self.function_stack.append(name)
        self.generic_visit(node)
        self.function_stack.pop()
