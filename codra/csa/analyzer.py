from __future__ import annotations

import ast
import builtins
import sys
from dataclasses import dataclass

from ..function.symbol_collector import FunctionSymbolCollector
from ..function.symbol_usage import FunctionSymbolUsage
from ..module.symbol_collector import ModuleSymbolCollector
from ..unit.node import UnitNode
from ..unit.node_collector import UnitNodeCollector
from .result import CsaResult


@dataclass
class CsaAnalyzer:
    def analyze_file(self, file_path: str) -> list[CsaResult]:
        tree = self._parse_file(file_path)
        module_symbols = self._collect_module_symbols(tree)
        builtin_names = set(dir(builtins))
        stdlib_modules = set(sys.stdlib_module_names)
        unit_nodes = self._collect_unit_nodes(tree, file_path)
        return self._build_results(
            unit_nodes,
            module_symbols,
            builtin_names,
            stdlib_modules,
        )

    def _parse_file(self, file_path: str) -> ast.AST:
        with open(file_path, "r", encoding="utf-8") as handle:
            source = handle.read()
        return ast.parse(source, filename=file_path)

    def _collect_module_symbols(self, tree: ast.AST) -> set[str]:
        return ModuleSymbolCollector().collect(tree)

    def _collect_unit_nodes(self, tree: ast.AST, file_path: str) -> list[UnitNode]:
        unit_collector = UnitNodeCollector(file_path=file_path)
        unit_collector.visit(tree)
        return unit_collector.units

    def _extract_external_symbols(
        self,
        usage: FunctionSymbolUsage,
        module_symbols: set[str],
        builtin_names: set[str],
        stdlib_modules: set[str],
    ) -> set[str]:
        used_names = usage.used_names
        local_names = usage.locals
        global_symbols = used_names.intersection(module_symbols) - local_names
        free_symbols = used_names - local_names - module_symbols
        external_symbols = global_symbols.union(free_symbols)
        return {
            symbol
            for symbol in external_symbols
            if symbol not in builtin_names and symbol not in stdlib_modules
        }

    def _build_results(
        self,
        unit_nodes: list[UnitNode],
        module_symbols: set[str],
        builtin_names: set[str],
        stdlib_modules: set[str],
    ) -> list[CsaResult]:
        results: list[CsaResult] = []
        for unit_node in unit_nodes:
            usage = FunctionSymbolCollector().collect(unit_node.node)
            external_symbols = self._extract_external_symbols(
                usage, module_symbols, builtin_names, stdlib_modules
            )
            results.append(
                CsaResult(
                    unit=unit_node.definition,
                    csa_main=len(external_symbols),
                    external_symbols=sorted(external_symbols),
                    self_fields_read=sorted(usage.self_fields_read),
                )
            )
        return results
