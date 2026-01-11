import builtins
import sys
import tempfile
import textwrap
import unittest

from codra.bps.analyzer import BpsAnalyzer
from codra.bps.result import BpsResult
from codra.csa.analyzer import CsaAnalyzer
from codra.csa.result import CsaResult
from codra.function.symbol_collector import FunctionSymbolCollector
from codra.indirection.analyzer import (
    IndirectionAnalyzer,
    collect_calls_by_unit,
    resolve_alias,
)
from codra.indirection.result import IndirectionResult
from codra.report.builder import ReportBuilder
from codra.unit.definition import UnitDefinition
from codra.unit.node_collector import UnitNodeCollector
from codra.unit.overview import UnitReport


class BpsAnalyzerHelperTests(unittest.TestCase):
    def test_helpers_collect_bps_scores(self) -> None:
        source = textwrap.dedent(
            """
            def foo(x):
                if x and y:
                    return 1
                return 2
            """
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = f"{tmpdir}/sample.py"
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(source)
            analyzer = BpsAnalyzer()
            tree = analyzer._parse_file(file_path)
            unit_nodes = analyzer._collect_units(tree, file_path)
            self.assertEqual(len(unit_nodes), 1)
            bps = analyzer._collect_bps(unit_nodes[0])
            self.assertAlmostEqual(bps, 0.25)
            results = analyzer._build_results(unit_nodes, [bps])
            self.assertEqual(results, [BpsResult(unit=unit_nodes[0].definition, bps=bps)])


class CsaAnalyzerHelperTests(unittest.TestCase):
    def test_helpers_extract_external_symbols(self) -> None:
        source = textwrap.dedent(
            """
            import os
            from math import sqrt

            CONST = 10

            def foo(self, x):
                return self.attr + sqrt(x) + CONST + y
            """
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = f"{tmpdir}/sample.py"
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(source)
            analyzer = CsaAnalyzer()
            tree = analyzer._parse_file(file_path)
            module_symbols = analyzer._collect_module_symbols(tree)
            unit_nodes = analyzer._collect_unit_nodes(tree, file_path)
            usage = FunctionSymbolCollector().collect(unit_nodes[0].node)
            external_symbols = analyzer._extract_external_symbols(
                usage,
                module_symbols,
                set(dir(builtins)),
                set(sys.stdlib_module_names),
            )
            self.assertEqual(external_symbols, {"CONST", "sqrt", "y"})
            results = analyzer._build_results(
                unit_nodes,
                module_symbols,
                set(dir(builtins)),
                set(sys.stdlib_module_names),
            )
            self.assertEqual(
                results,
                [
                    CsaResult(
                        unit=unit_nodes[0].definition,
                        csa_main=3,
                        external_symbols=["CONST", "sqrt", "y"],
                        self_fields_read=["attr"],
                    )
                ],
            )


class IndirectionAnalyzerHelperTests(unittest.TestCase):
    def test_helpers_collect_call_graph_and_depth(self) -> None:
        source = textwrap.dedent(
            """
            def bar():
                pass

            def foo():
                bar()

            alias = bar

            def baz():
                alias()
            """
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = f"{tmpdir}/sample.py"
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(source)
            analyzer = IndirectionAnalyzer()
            tree = analyzer._parse_file(file_path)
            function_names = analyzer._collect_function_definitions(tree)
            self.assertEqual(function_names, {"bar", "foo", "baz"})
            aliases = analyzer._collect_aliases(tree)
            self.assertEqual(aliases, {"alias": "bar"})
            class_methods = analyzer._collect_class_methods(tree)
            unit_collector = UnitNodeCollector(file_path=file_path)
            unit_collector.visit(tree)
            call_map = collect_calls_by_unit(unit_collector.units)
            call_graph = analyzer._collect_call_graph(
                function_names, class_methods, aliases, call_map, {}
            )
            self.assertEqual(call_graph["foo"], ["bar"])
            self.assertEqual(call_graph["baz"], ["bar"])
            id_max, id_avg = analyzer._calculate_indirection_depths(
                ["bar"], call_graph, {}
            )
            self.assertEqual(id_max, 1)
            self.assertEqual(id_avg, 1.0)

    def test_helpers_resolve_alias_chain_and_class_methods(self) -> None:
        source = textwrap.dedent(
            """
            def helper():
                pass

            alias = helper
            alias2 = alias

            def uses_alias():
                alias2()

            class Foo:
                def ping(self):
                    self.pong()
                    alias2()

                def pong(self):
                    alias()
            """
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = f"{tmpdir}/sample.py"
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(source)
            analyzer = IndirectionAnalyzer()
            tree = analyzer._parse_file(file_path)
            aliases = analyzer._collect_aliases(tree)
            self.assertEqual(resolve_alias("alias2", aliases), "helper")
            function_names = analyzer._collect_function_definitions(tree)
            class_methods = analyzer._collect_class_methods(tree)
            unit_collector = UnitNodeCollector(file_path=file_path)
            unit_collector.visit(tree)
            call_map = collect_calls_by_unit(unit_collector.units)
            call_graph = analyzer._collect_call_graph(
                function_names, class_methods, aliases, call_map, {}
            )
            self.assertEqual(call_graph["uses_alias"], ["helper"])
            self.assertEqual(
                call_graph["Foo.ping"], ["Foo.pong", "helper"]
            )
            results = analyzer.analyze_file(file_path)
            results_by_unit = {result.unit.qualified_id: result for result in results}
            self.assertEqual(results_by_unit["uses_alias"].id_max, 1)
            self.assertEqual(results_by_unit["Foo.ping"].id_max, 2)


class ReportBuilderHelperTests(unittest.TestCase):
    def test_helpers_build_file_report_and_summary(self) -> None:
        builder = ReportBuilder(
            csa_analyzer=CsaAnalyzer(),
            indirection_analyzer=IndirectionAnalyzer(),
            bps_analyzer=BpsAnalyzer(),
            path_collector=None,
        )
        file_path = "sample.py"
        unit_a = UnitDefinition(
            file_path=file_path,
            qualified_id="a",
            kind="function",
            start_line=1,
            end_line=2,
        )
        unit_b = UnitDefinition(
            file_path=file_path,
            qualified_id="b",
            kind="function",
            start_line=3,
            end_line=4,
        )
        csa_results = [
            CsaResult(
                unit=unit_b,
                csa_main=1,
                external_symbols=["z"],
                self_fields_read=[],
            )
        ]
        indirection_results = [
            IndirectionResult(
                unit=unit_a, id_max=2, id_avg=1.5, unresolved_calls=["x"]
            )
        ]
        bps_results = [BpsResult(unit=unit_a, bps=0.5), BpsResult(unit=unit_b, bps=1.0)]
        file_report, unit_count = builder._build_file_report(
            file_path, csa_results, indirection_results, bps_results
        )
        self.assertEqual(unit_count, 2)
        self.assertEqual(file_report.file_path, file_path)
        self.assertEqual(
            [unit.unit.qualified_id for unit in file_report.units], ["a", "b"]
        )
        unit_a_report, unit_b_report = file_report.units
        self.assertIsInstance(unit_a_report, UnitReport)
        self.assertEqual(unit_a_report.metrics.id_max, 2)
        self.assertEqual(unit_b_report.metrics.csa_main, 1)
        summary = builder._build_summary([file_report], unit_count)
        self.assertEqual(summary.total_files, 1)
        self.assertEqual(summary.total_units, 2)


if __name__ == "__main__":
    unittest.main()
