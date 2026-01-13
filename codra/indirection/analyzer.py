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
        builtin_names = self._collect_builtin_names()
        stdlib_modules = self._collect_stdlib_modules()
        unit_nodes, call_map = self._collect_unit_calls(file_path, tree)
        alias_cache: dict[str, str] = {}
        call_graph = self._collect_call_graph(
            function_names, class_methods, aliases, call_map, alias_cache
        )
        return self._build_results(
            unit_nodes=unit_nodes,
            call_map=call_map,
            class_methods=class_methods,
            aliases=aliases,
            function_names=function_names,
            module_symbols=module_symbols,
            builtin_names=builtin_names,
            stdlib_modules=stdlib_modules,
            alias_cache=alias_cache,
            call_graph=call_graph,
        )

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

    def _collect_builtin_names(self) -> set[str]:
        return set(dir(builtins))

    def _collect_stdlib_modules(self) -> set[str]:
        return set(sys.stdlib_module_names)

    def _collect_unit_calls(
        self, file_path: str, tree: ast.AST
    ) -> tuple[list[UnitNode], dict[str, list[str]]]:
        unit_collector = UnitNodeCollector(file_path=file_path)
        unit_collector.visit(tree)
        call_map = collect_calls_by_unit(unit_collector.units)
        return unit_collector.units, call_map

    def _build_results(
        self,
        unit_nodes: list[UnitNode],
        call_map: dict[str, list[str]],
        class_methods: dict[str, set[str]],
        aliases: dict[str, str],
        function_names: set[str],
        module_symbols: set[str],
        builtin_names: set[str],
        stdlib_modules: set[str],
        alias_cache: dict[str, str],
        call_graph: dict[str, list[str]],
    ) -> list[IndirectionResult]:
        depth_cache: dict[str, int] = {}
        results: list[IndirectionResult] = []
        for unit_node in unit_nodes:
            class_name, class_method_names = self._class_context(
                unit_node, class_methods
            )
            call_names = call_map.get(unit_node.definition.qualified_id, [])
            resolved_calls, unresolved_calls = self._resolve_unit_calls(
                call_names=call_names,
                class_name=class_name,
                class_method_names=class_method_names,
                aliases=aliases,
                alias_cache=alias_cache,
                function_names=function_names,
                module_symbols=module_symbols,
                builtin_names=builtin_names,
                stdlib_modules=stdlib_modules,
            )
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

    def _class_context(
        self, unit_node: UnitNode, class_methods: dict[str, set[str]]
    ) -> tuple[str | None, set[str]]:
        if unit_node.definition.kind != "method":
            return None, set()
        class_name = unit_node.definition.qualified_id.split(".", 1)[0]
        return class_name, class_methods.get(class_name, set())

    def _resolve_unit_calls(
        self,
        call_names: list[str],
        class_name: str | None,
        class_method_names: set[str],
        aliases: dict[str, str],
        alias_cache: dict[str, str],
        function_names: set[str],
        module_symbols: set[str],
        builtin_names: set[str],
        stdlib_modules: set[str],
    ) -> tuple[list[str], set[str]]:
        resolved_calls: list[str] = []
        unresolved_calls: set[str] = set()
        for name in call_names:
            resolved_self = self._resolve_self_call(
                name, class_name, class_method_names
            )
            if resolved_self:
                resolved_calls.append(resolved_self)
                continue
            if name.startswith("self."):
                continue
            resolved = self._resolve_alias(name, aliases, alias_cache)
            if resolved in function_names:
                resolved_calls.append(resolved)
                continue
            if self._is_ignorable_call(
                resolved, module_symbols, builtin_names, stdlib_modules
            ):
                continue
            unresolved_calls.add(name)
        return resolved_calls, unresolved_calls

    def _resolve_self_call(
        self,
        name: str,
        class_name: str | None,
        class_method_names: set[str],
    ) -> str | None:
        if not name.startswith("self."):
            return None
        if not class_name:
            return None
        method_name = name.split(".", 1)[1]
        if method_name not in class_method_names:
            return None
        return f"{class_name}.{method_name}"

    def _is_ignorable_call(
        self,
        resolved: str,
        module_symbols: set[str],
        builtin_names: set[str],
        stdlib_modules: set[str],
    ) -> bool:
        return (
            resolved in module_symbols
            or resolved in builtin_names
            or resolved in stdlib_modules
        )

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
