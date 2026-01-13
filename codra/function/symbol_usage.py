from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FunctionSymbolUsage:
    locals: set[str] = field(default_factory=set)
    used_names: set[str] = field(default_factory=set)
    self_fields_read: set[str] = field(default_factory=set)
    global_decls: set[str] = field(default_factory=set)
    nonlocal_decls: set[str] = field(default_factory=set)
