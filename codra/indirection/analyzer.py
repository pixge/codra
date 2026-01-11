from __future__ import annotations

import ast
import builtins
import sys
from dataclasses import dataclass

from ..alias.collector import AliasCollector
from ..call.collector import CallCollector
from ..function.definition_collector import FunctionDefinitionCollector
from ..module.symbol_collector import ModuleSymbolCollector
from ..unit.node_collector import UnitNodeCollector
from .result import IndirectionResult


@dataclass
class IndirectionAnalyzer:
    def analyze_file(self, file_path: str) -> list[IndirectionResult]:
        with open(file_path, "r", encoding="utf-8") as handle:
            source = handle.read()
        tree = ast.parse(source, filename=file_path)
        function_names = FunctionDefinitionCollector().collect(tree)
        class_methods = self._collect_class_methods(tree)
        aliases = AliasCollector().collect(tree)
        module_symbols = ModuleSymbolCollector().collect(tree)
        builtin_names = set(dir(builtins))
        stdlib_modules = set(sys.stdlib_module_names)
        call_graph = self._build_call_graph(tree, function_names, class_methods, aliases)
        depth_cache: dict[str, int] = {}
        results: list[IndirectionResult] = []
        unit_collector = UnitNodeCollector(file_path=file_path)
        unit_collector.visit(tree)
        for unit_node in unit_collector.units:
            class_name = (
                unit_node.definition.qualified_id.split(".", 1)[0]
                if unit_node.definition.kind == "method"
                else None
            )
            call_names = CallCollector().collect(unit_node.node)
            resolved_calls: list[str] = []
            unresolved_calls: set[str] = set()
            for name in call_names:
                if name.startswith("self.") and class_name:
                    method_name = name.split(".", 1)[1]
                    if method_name in class_methods.get(class_name, set()):
                        resolved_calls.append(f"{class_name}.{method_name}")
                        continue
                resolved = self._resolve_alias(name, aliases)
                if resolved in function_names:
                    resolved_calls.append(resolved)
                elif resolved in module_symbols:
                    continue
                elif resolved in builtin_names:
                    continue
                elif resolved in stdlib_modules:
                    continue
                else:
                    unresolved_calls.add(name)
            call_depths = [
                1 + self._depth(call_name, call_graph, depth_cache)
                for call_name in resolved_calls
            ]
            if call_depths:
                id_max = max(call_depths)
                id_avg = sum(call_depths) / len(call_depths)
            else:
                id_max = 0
                id_avg = 0.0
            results.append(
                IndirectionResult(
                    unit=unit_node.definition,
                    id_max=id_max,
                    id_avg=id_avg,
                    unresolved_calls=sorted(unresolved_calls),
                )
            )
        return results

    def _collect_class_methods(self, tree: ast.AST) -> dict[str, set[str]]:
        class_methods: dict[str, set[str]] = {}
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                methods = {
                    statement.name
                    for statement in node.body
                    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
                class_methods[node.name] = methods
        return class_methods

    def _build_call_graph(
        self,
        tree: ast.AST,
        function_names: set[str],
        class_methods: dict[str, set[str]],
        aliases: dict[str, str],
    ) -> dict[str, list[str]]:
        call_graph: dict[str, list[str]] = {name: [] for name in function_names}
        for class_name, methods in class_methods.items():
            for method_name in methods:
                call_graph[f"{class_name}.{method_name}"] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in function_names:
                    call_names = CallCollector().collect(node)
                    for name in call_names:
                        resolved = self._resolve_alias(name, aliases)
                        if resolved in function_names:
                            call_graph[node.name].append(resolved)
            elif isinstance(node, ast.ClassDef):
                methods = class_methods.get(node.name, set())
                for statement in node.body:
                    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        qualified_name = f"{node.name}.{statement.name}"
                        if qualified_name not in call_graph:
                            continue
                        call_names = CallCollector().collect(statement)
                        for name in call_names:
                            if name.startswith("self."):
                                method_name = name.split(".", 1)[1]
                                if method_name in methods:
                                    call_graph[qualified_name].append(
                                        f"{node.name}.{method_name}"
                                    )
                            else:
                                resolved = self._resolve_alias(name, aliases)
                                if resolved in function_names:
                                    call_graph[qualified_name].append(resolved)
        return call_graph

    def _resolve_alias(self, name: str, aliases: dict[str, str]) -> str:
        seen: set[str] = set()
        current = name
        while current in aliases and current not in seen:
            seen.add(current)
            current = aliases[current]
        return current

    def _depth(
        self,
        name: str,
        call_graph: dict[str, list[str]],
        depth_cache: dict[str, int],
    ) -> int:
        if name in depth_cache:
            return depth_cache[name]
        if name not in call_graph:
            depth_cache[name] = 0
            return 0
        if not call_graph[name]:
            depth_cache[name] = 0
            return 0
        depth_cache[name] = -1
        depth = 0
        for callee in call_graph[name]:
            if depth_cache.get(callee) == -1:
                continue
            depth = max(depth, 1 + self._depth(callee, call_graph, depth_cache))
        depth_cache[name] = depth
        return depth
