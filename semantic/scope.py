from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Symbol:
    name: str
    kind: str  # "var" | "func" | "type" | "enum"
    data: Any  # type info, param list, etc.

class Scope:
    def __init__(self, parent: Optional["Scope"]=None):
        self.parent = parent
        self.table: Dict[str, Symbol] = {}

    def define(self, sym: Symbol) -> None:
        if sym.name in self.table:
            raise KeyError(sym.name)
        self.table[sym.name] = sym

    def lookup(self, name: str) -> Optional[Symbol]:
        s = self
        while s is not None:
            if name in s.table:
                return s.table[name]
            s = s.parent
        return None