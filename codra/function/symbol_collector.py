from __future__ import annotations

import ast
from ast import NodeVisitor
from dataclasses import dataclass, field

from .symbol_usage import FunctionSymbolUsage


@dataclass
class FunctionSymbolCollector(NodeVisitor):
    """AST visitor collecting symbol usage via NodeVisitor."""
    usage: FunctionSymbolUsage = field(default_factory=FunctionSymbolUsage)

    def collect(self, node: ast.AST) -> FunctionSymbolUsage:
        self._add_arguments(node)
        for statement in node.body:
            super().visit(statement)
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
        context = node.ctx
        name = node.id
        if self._is_load_context(context):
            self.usage.used_names.add(name)
        elif self._is_store_or_del_context(context):
            if self._is_declared_nonlocal_or_global(name):
                return
            self.usage.locals.add(name)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if self._is_self_attribute_read(node):
            self.usage.self_fields_read.add(node.attr)
        super().generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        handler_name = node.name
        if self._is_exception_name(handler_name):
            self.usage.locals.add(handler_name)
        elif handler_name is not None:
            super().visit(handler_name)
        for statement in node.body:
            super().visit(statement)

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

    def _is_load_context(self, context: ast.expr_context) -> bool:
        return isinstance(context, ast.Load)

    def _is_store_or_del_context(self, context: ast.expr_context) -> bool:
        return isinstance(context, (ast.Store, ast.Del))

    def _is_declared_nonlocal_or_global(self, name: str) -> bool:
        is_global = name in self.usage.global_decls
        is_nonlocal = name in self.usage.nonlocal_decls
        return is_global or is_nonlocal

    def _is_self_attribute_read(self, node: ast.Attribute) -> bool:
        context = node.ctx
        if not self._is_load_context(context):
            return False
        value = node.value
        return isinstance(value, ast.Name) and value.id == "self"

    def _is_exception_name(self, name: object) -> bool:
        return isinstance(name, str)
