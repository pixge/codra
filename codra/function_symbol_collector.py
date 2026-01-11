from __future__ import annotations

import ast
from dataclasses import dataclass, field

from .function_symbol_usage import FunctionSymbolUsage


@dataclass
class FunctionSymbolCollector(ast.NodeVisitor):
    usage: FunctionSymbolUsage = field(default_factory=FunctionSymbolUsage)

    def collect(self, node: ast.AST) -> FunctionSymbolUsage:
        self._add_arguments(node)
        for statement in node.body:
            self.visit(statement)
        return self.usage

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return None

    def visit_Global(self, node: ast.Global) -> None:
        self.usage.global_decls.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.usage.nonlocal_decls.update(node.names)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.usage.used_names.add(node.id)
        elif isinstance(node.ctx, (ast.Store, ast.Del)):
            if node.id in self.usage.global_decls:
                return
            if node.id in self.usage.nonlocal_decls:
                return
            self.usage.locals.add(node.id)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.ctx, ast.Load):
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                self.usage.self_fields_read.add(node.attr)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if isinstance(node.name, str):
            self.usage.locals.add(node.name)
        elif node.name is not None:
            self.visit(node.name)
        for statement in node.body:
            self.visit(statement)

    def _add_arguments(self, node: ast.AST) -> None:
        arguments = node.args
        for arg in arguments.posonlyargs:
            self.usage.locals.add(arg.arg)
        for arg in arguments.args:
            self.usage.locals.add(arg.arg)
        for arg in arguments.kwonlyargs:
            self.usage.locals.add(arg.arg)
        if arguments.vararg is not None:
            self.usage.locals.add(arguments.vararg.arg)
        if arguments.kwarg is not None:
            self.usage.locals.add(arguments.kwarg.arg)
