from __future__ import annotations

import ast
from dataclasses import dataclass

from .csa_result import CsaResult
from .function_symbol_collector import FunctionSymbolCollector
from .module_symbol_collector import ModuleSymbolCollector
from .unit_node_collector import UnitNodeCollector


@dataclass
class CsaAnalyzer:
    def analyze_file(self, file_path: str) -> list[CsaResult]:
        with open(file_path, "r", encoding="utf-8") as handle:
            source = handle.read()
        tree = ast.parse(source, filename=file_path)
        module_symbols = ModuleSymbolCollector().collect(tree)
        unit_collector = UnitNodeCollector(file_path=file_path)
        unit_collector.visit(tree)
        results: list[CsaResult] = []
        for unit_node in unit_collector.units:
            usage = FunctionSymbolCollector().collect(unit_node.node)
            used_names = usage.used_names
            local_names = usage.locals
            global_symbols = used_names.intersection(module_symbols) - local_names
            free_symbols = used_names - local_names - module_symbols
            external_symbols = global_symbols.union(free_symbols)
            results.append(
                CsaResult(
                    unit=unit_node.definition,
                    csa_main=len(external_symbols),
                    external_symbols=sorted(external_symbols),
                    self_fields_read=sorted(usage.self_fields_read),
                )
            )
        return results
