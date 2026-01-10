from __future__ import annotations

import ast
from dataclasses import dataclass

from .alias_collector import AliasCollector
from .call_collector import CallCollector
from .function_definition_collector import FunctionDefinitionCollector
from .indirection_result import IndirectionResult
from .unit_node_collector import UnitNodeCollector


@dataclass
class IndirectionAnalyzer:
    def analyze_file(self, file_path: str) -> list[IndirectionResult]:
        with open(file_path, "r", encoding="utf-8") as handle:
            source = handle.read()
        tree = ast.parse(source, filename=file_path)
        function_names = FunctionDefinitionCollector().collect(tree)
        aliases = AliasCollector().collect(tree)
        call_graph = self._build_call_graph(tree, function_names, aliases)
        depth_cache: dict[str, int] = {}
        results: list[IndirectionResult] = []
        unit_collector = UnitNodeCollector(file_path=file_path)
        unit_collector.visit(tree)
        for unit_node in unit_collector.units:
            call_names = CallCollector().collect(unit_node.node)
            resolved_calls: list[str] = []
            unresolved_calls: set[str] = set()
            for name in call_names:
                resolved = self._resolve_alias(name, aliases)
                if resolved in function_names:
                    resolved_calls.append(resolved)
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

    def _build_call_graph(
        self,
        tree: ast.AST,
        function_names: set[str],
        aliases: dict[str, str],
    ) -> dict[str, list[str]]:
        call_graph: dict[str, list[str]] = {name: [] for name in function_names}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in function_names:
                    call_names = CallCollector().collect(node)
                    for name in call_names:
                        resolved = self._resolve_alias(name, aliases)
                        if resolved in function_names:
                            call_graph[node.name].append(resolved)
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
