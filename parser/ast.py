from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict
from enum import Enum, auto

# Узлы AST: Program, ExprStmt, BinOp, UnOp, Literal, Ident

class OpKind(Enum):
    # бинарные
    OR = auto()      # ||
    AND = auto()     # &&
    EQ = auto()      # ==
    NEQ = auto()     # !=
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    # унарные
    NEG = auto()     # -x
    NOT = auto()     # !x


_id_counter = 0
def _next_id() -> int:
    global _id_counter
    _id_counter += 1
    return _id_counter


@dataclass
class Node:
    id: int = field(default_factory=_next_id, init=False)

    def to_json(self) -> Dict[str, Any]:
        raise NotImplementedError

    def pretty(self, indent: int = 0) -> str:
        raise NotImplementedError


@dataclass
class Program(Node):
    stmts: List["ExprStmt"] = field(default_factory=list)

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": "Program",
            "id": self.id,
            "stmts": [s.to_json() for s in self.stmts],
        }

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}Program#{self.id}\n"
        for st in self.stmts:
            s += st.pretty(indent + 1)
        return s


@dataclass
class ExprStmt(Node):
    expr: "Expr" = None

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": "ExprStmt",
            "id": self.id,
            "expr": self.expr.to_json() if self.expr else None,
        }

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}ExprStmt#{self.id}\n{self.expr.pretty(indent + 1)}"


# База для выражений
class Expr(Node):
    pass


@dataclass
class BinOp(Expr):
    op: OpKind = None
    left: Expr = None
    right: Expr = None

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": "BinOp",
            "id": self.id,
            "op": self.op.name,
            "left": self.left.to_json(),
            "right": self.right.to_json(),
        }

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}BinOp#{self.id}({self.op.name})\n"
        s += self.left.pretty(indent + 1)
        s += self.right.pretty(indent + 1)
        return s


@dataclass
class UnOp(Expr):
    op: OpKind = None
    operand: Expr = None

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": "UnOp",
            "id": self.id,
            "op": self.op.name,
            "operand": self.operand.to_json(),
        }

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}UnOp#{self.id}({self.op.name})\n"
        s += self.operand.pretty(indent + 1)
        return s


@dataclass
class Literal(Expr):
    value: Any = None
    kind: str = ""  # "int" | "real" | "bool"

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": "Literal",
            "id": self.id,
            "kind": self.kind,
            "value": self.value,
        }

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}Literal#{self.id}({self.kind}={self.value})\n"


@dataclass
class Ident(Expr):
    name: str = ""

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": "Ident",
            "id": self.id,
            "name": self.name,
        }

    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}Ident#{self.id}({self.name})\n"
