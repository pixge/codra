from __future__ import annotations

import ast
from dataclasses import dataclass

from .definition import UnitDefinition


@dataclass(frozen=True)
class UnitNode:
    definition: UnitDefinition
    node: ast.AST
