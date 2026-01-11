from __future__ import annotations

import ast
import builtins
import sys
from dataclasses import dataclass
from typing import Iterable, Mapping

from ..alias.collector import AliasCollector
from ..call.collector import CallCollector
from ..function.definition_collector import FunctionDefinitionCollector
from ..module.symbol_collector import ModuleSymbolCollector
from ..unit.node import UnitNode
from ..unit.node_collector import UnitNodeCollector
from .result import IndirectionResult


def resolve_alias(name: str, aliases: Mapping[str, str]) -> str:
    seen: set[str] = set()
    current = name
    while current in aliases and current not in seen:
        seen.add(current)
        current = aliases[current]
    return current


def collect_calls(node: ast.AST) -> list[str]:
    return CallCollector().collect(node)


def collect_calls_by_unit(unit_nodes: Iterable[UnitNode]) -> dict[str, list[str]]:
    return {
        unit.definition.qualified_id: collect_calls(unit.node)
        for unit in unit_nodes
    }


@dataclass
class IndirectionAnalyzer:
    def analyze_file(self, file_path: str) -> list[IndirectionResult]:
        tree = self._parse_file(file_path)
        function_names = self._collect_function_definitions(tree)
        class_methods = self._collect_class_methods(tree)
        aliases = self._collect_aliases(tree)
        module_symbols = ModuleSymbolCollector().collect(tree)
        builtin_names = set(dir(builtins))
        stdlib_modules = set(sys.stdlib_module_names)
        unit_collector = UnitNodeCollector(file_path=file_path)
        unit_collector.visit(tree)
        call_map = collect_calls_by_unit(unit_collector.units)
        alias_cache: dict[str, str] = {}
        call_graph = self._collect_call_graph(
            function_names, class_methods, aliases, call_map, alias_cache
        )
        depth_cache: dict[str, int] = {}
        results: list[IndirectionResult] = []
        for unit_node in unit_collector.units:
            class_name = (
                unit_node.definition.qualified_id.split(".", 1)[0]
                if unit_node.definition.kind == "method"
                else None
            )
            call_names = call_map.get(unit_node.definition.qualified_id, [])
            resolved_calls: list[str] = []
            unresolved_calls: set[str] = set()
            for name in call_names:
                if name.startswith("self."):
                    if class_name:
                        method_name = name.split(".", 1)[1]
                        if method_name in class_methods.get(class_name, set()):
                            resolved_calls.append(f"{class_name}.{method_name}")
                    continue
                resolved = self._resolve_alias(name, aliases, alias_cache)
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
            id_max, id_avg = self._calculate_indirection_depths(
                resolved_calls, call_graph, depth_cache
            )
            results.append(
                IndirectionResult(
                    unit=unit_node.definition,
                    id_max=id_max,
                    id_avg=id_avg,
                    unresolved_calls=sorted(unresolved_calls),
                )
            )
        return results

    def _parse_file(self, file_path: str) -> ast.AST:
        with open(file_path, "r", encoding="utf-8") as handle:
            source = handle.read()
        return ast.parse(source, filename=file_path)

    def _collect_function_definitions(self, tree: ast.AST) -> set[str]:
        return FunctionDefinitionCollector().collect(tree)

    def _collect_aliases(self, tree: ast.AST) -> dict[str, str]:
        return AliasCollector().collect(tree)

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

    def _collect_call_graph(
        self,
        function_names: set[str],
        class_methods: dict[str, set[str]],
        aliases: dict[str, str],
        call_map: dict[str, list[str]],
        alias_cache: dict[str, str],
    ) -> dict[str, list[str]]:
        call_graph: dict[str, list[str]] = {name: [] for name in function_names}
        for class_name, methods in class_methods.items():
            for method_name in methods:
                call_graph[f"{class_name}.{method_name}"] = []
        for function_name in function_names:
            call_names = call_map.get(function_name, [])
            for name in call_names:
                resolved = self._resolve_alias(name, aliases, alias_cache)
                if resolved in function_names:
                    call_graph[function_name].append(resolved)
        for class_name, methods in class_methods.items():
            for method_name in methods:
                qualified_name = f"{class_name}.{method_name}"
                call_names = call_map.get(qualified_name, [])
                for name in call_names:
                    if name.startswith("self."):
                        callee_name = name.split(".", 1)[1]
                        if callee_name in methods:
                            call_graph[qualified_name].append(
                                f"{class_name}.{callee_name}"
                            )
                    else:
                        resolved = self._resolve_alias(name, aliases, alias_cache)
                        if resolved in function_names:
                            call_graph[qualified_name].append(resolved)
        return call_graph

    def _resolve_alias(
        self, name: str, aliases: dict[str, str], alias_cache: dict[str, str]
    ) -> str:
        if name in alias_cache:
            return alias_cache[name]
        resolved = resolve_alias(name, aliases)
        alias_cache[name] = resolved
        return resolved

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

    def _calculate_indirection_depths(
        self,
        resolved_calls: list[str],
        call_graph: dict[str, list[str]],
        depth_cache: dict[str, int],
    ) -> tuple[int, float]:
        call_depths = [
            1 + self._depth(call_name, call_graph, depth_cache)
            for call_name in resolved_calls
        ]
        if not call_depths:
            return 0, 0.0
        return max(call_depths), sum(call_depths) / len(call_depths)
