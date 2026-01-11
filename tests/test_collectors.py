import ast
import unittest

from codra.alias.collector import AliasCollector
from codra.call.collector import CallCollector
from codra.condition.collector import ConditionMetricsCollector
from codra.function.definition_collector import FunctionDefinitionCollector
from codra.function.symbol_collector import FunctionSymbolCollector
from codra.if_.collector import IfCollector
from codra.module.symbol_collector import ModuleSymbolCollector
from codra.unit.node_collector import UnitNodeCollector


class CollectorVisitTests(unittest.TestCase):
    def test_alias_collector_tracks_top_level_aliases(self) -> None:
        tree = ast.parse(
            """
alias = original
other: int = alias

def inner():
    shadow = original
"""
        )
        collector = AliasCollector()
        self.assertEqual(
            collector.collect(tree),
            {"alias": "original", "other": "alias"},
        )

    def test_call_collector_tracks_module_calls_only(self) -> None:
        tree = ast.parse(
            """
foo()
self.bar()

def inner():
    baz()

class Thing:
    def method(self):
        qux()
"""
        )
        collector = CallCollector()
        self.assertEqual(collector.collect(tree), ["foo", "self.bar"])

    def test_condition_metrics_collector_counts_operations(self) -> None:
        tree = ast.parse(
            """
if a and b and c and foo(x) and y < z:
    pass
"""
        )
        if_node = tree.body[0]
        collector = ConditionMetricsCollector(
            local_names={"a", "b", "c", "x", "y", "z"}
        )
        metrics = collector.collect(if_node.test)
        self.assertEqual(metrics.bool_ops, 4)
        self.assertEqual(metrics.compare_ops, 1)
        self.assertEqual(metrics.calls, 1)
        self.assertEqual(metrics.external_refs, 1)

    def test_if_collector_tracks_module_if_statements(self) -> None:
        tree = ast.parse(
            """
if ready:
    pass

def inner():
    if nested:
        pass
"""
        )
        collector = IfCollector()
        nodes = collector.collect(tree)
        self.assertEqual(len(nodes), 1)
        self.assertIsInstance(nodes[0], ast.If)

    def test_function_definition_collector_skips_methods(self) -> None:
        tree = ast.parse(
            """
def top():
    def inner():
        return 1
    return inner()

class Thing:
    def method(self):
        return 2
"""
        )
        collector = FunctionDefinitionCollector()
        self.assertEqual(collector.collect(tree), {"top", "inner"})

    def test_function_symbol_collector_tracks_usage(self) -> None:
        tree = ast.parse(
            """
def foo(arg):
    global g
    x = arg
    self.attr
    return g + x
"""
        )
        function_node = next(
            node for node in tree.body if isinstance(node, ast.FunctionDef)
        )
        collector = FunctionSymbolCollector()
        usage = collector.collect(function_node)
        self.assertIn("arg", usage.locals)
        self.assertIn("x", usage.locals)
        self.assertIn("g", usage.used_names)
        self.assertIn("arg", usage.used_names)
        self.assertIn("attr", usage.self_fields_read)
        self.assertIn("g", usage.global_decls)

    def test_module_symbol_collector_gathers_symbols(self) -> None:
        tree = ast.parse(
            """
import os as operating
from sys import path as sys_path

class Foo:
    pass

def bar():
    pass

baz = 1
count: int = 2

for i in range(3):
    pass

with open("a") as f:
    pass

try:
    pass
except Exception as exc:
    pass
"""
        )
        collector = ModuleSymbolCollector()
        symbols = collector.collect(tree)
        self.assertTrue(
            {"operating", "sys_path", "Foo", "bar", "baz", "count", "i", "f", "exc"}
            <= symbols
        )

    def test_unit_node_collector_builds_qualified_ids(self) -> None:
        tree = ast.parse(
            """
def top():
    def inner():
        return 1
    return inner()

class Thing:
    def method(self):
        return 2
"""
        )
        collector = UnitNodeCollector(file_path="module.py")
        collector.visit(tree)
        qualified_ids = {unit.definition.qualified_id for unit in collector.units}
        kinds = {unit.definition.qualified_id: unit.definition.kind for unit in collector.units}
        self.assertEqual(qualified_ids, {"top", "top.inner", "Thing.method"})
        self.assertEqual(kinds["Thing.method"], "method")
        self.assertEqual(kinds["top"], "function")


if __name__ == "__main__":
    unittest.main()
