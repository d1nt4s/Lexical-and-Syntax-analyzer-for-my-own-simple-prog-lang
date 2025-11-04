from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from enum import Enum, auto

# === Выражения (из Этапа 3) ===

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
    NEG = auto()     # -
    NOT = auto()     # !

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

# --- Exprs ---
class Expr(Node):
    pass

@dataclass
class BinOp(Expr):
    op: OpKind = OpKind.ADD
    left: Expr = None
    right: Expr = None
    def to_json(self) -> Dict[str, Any]:
        return {"type": "BinOp", "id": self.id, "op": self.op.name,
                "left": self.left.to_json(), "right": self.right.to_json()}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}BinOp#{self.id}({self.op.name})\n" + \
               self.left.pretty(indent + 1) + self.right.pretty(indent + 1)

@dataclass
class UnOp(Expr):
    op: OpKind = OpKind.NEG
    expr: Expr = None
    def to_json(self) -> Dict[str, Any]:
        return {"type": "UnOp", "id": self.id, "op": self.op.name,
                "expr": self.expr.to_json()}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}UnOp#{self.id}({self.op.name})\n" + self.expr.pretty(indent + 1)

@dataclass
class Literal(Expr):
    value: Any = None
    def to_json(self) -> Dict[str, Any]:
        return {"type": "Literal", "id": self.id, "value": self.value}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}Literal#{self.id}({self.value!r})\n"

@dataclass
class Ident(Expr):
    name: str = ""
    def to_json(self) -> Dict[str, Any]:
        return {"type": "Ident", "id": self.id, "name": self.name}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}Ident#{self.id}({self.name})\n"

# === Операторы и верхний уровень (Этап 4) ===

class TypeKind(Enum):
    INT = auto()
    REAL = auto()
    BOOL = auto()

class Stmt(Node):
    pass

@dataclass
class ExprStmt(Stmt):
    expr: Expr = None
    def to_json(self) -> Dict[str, Any]:
        return {"type": "ExprStmt", "id": self.id, "expr": self.expr.to_json()}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}ExprStmt#{self.id}\n" + self.expr.pretty(indent + 1)

@dataclass
class Block(Stmt):
    stmts: List[Stmt] = field(default_factory=list)
    def to_json(self) -> Dict[str, Any]:
        return {"type": "Block", "id": self.id, "stmts": [s.to_json() for s in self.stmts]}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}Block#{self.id}\n"
        for st in self.stmts: s += st.pretty(indent + 1)
        return s

@dataclass
class Decl(Stmt):
    type: TypeKind = TypeKind.INT
    name: str = ""
    init: Optional[Expr] = None
    def to_json(self) -> Dict[str, Any]:
        obj = {"type": "Decl", "id": self.id, "decl_type": self.type.name, "name": self.name}
        if self.init is not None: obj["init"] = self.init.to_json()
        return obj
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}Decl#{self.id}({self.type.name} {self.name})\n"
        if self.init: s += self.init.pretty(indent + 1)
        return s

@dataclass
class Assign(Stmt):
    name: str = ""
    expr: Expr = None
    def to_json(self) -> Dict[str, Any]:
        return {"type": "Assign", "id": self.id, "name": self.name, "expr": self.expr.to_json()}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}Assign#{self.id}({self.name})\n" + self.expr.pretty(indent + 1)

@dataclass
class If(Stmt):
    cond: Expr = None
    then_branch: Stmt = None
    else_branch: Optional[Stmt] = None
    def to_json(self) -> Dict[str, Any]:
        obj = {"type": "If", "id": self.id,
               "cond": self.cond.to_json(),
               "then": self.then_branch.to_json()}
        if self.else_branch is not None: obj["else"] = self.else_branch.to_json()
        return obj
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}If#{self.id}\n" + self.cond.pretty(indent + 1) + self.then_branch.pretty(indent + 1)
        if self.else_branch: s += self.else_branch.pretty(indent + 1)
        return s

@dataclass
class For(Stmt):
    init: Stmt = None          # Decl | Assign
    cond: Optional[Expr] = None
    step: Optional[Assign] = None
    body: Stmt = None
    def to_json(self) -> Dict[str, Any]:
        obj = {"type": "For", "id": self.id,
               "init": self.init.to_json(),
               "body": self.body.to_json()}
        if self.cond is not None: obj["cond"] = self.cond.to_json()
        if self.step is not None: obj["step"] = self.step.to_json()
        return obj
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}For#{self.id}\n"
        s += self.init.pretty(indent + 1)
        if self.cond: s += self.cond.pretty(indent + 1)
        if self.step: s += self.step.pretty(indent + 1)
        s += self.body.pretty(indent + 1)
        return s

@dataclass
class PrintStmt(Stmt):
    expr: Expr = None
    def to_json(self) -> Dict[str, Any]:
        return {"type": "Print", "id": self.id, "expr": self.expr.to_json()}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}Print#{self.id}\n" + self.expr.pretty(indent + 1)

@dataclass
class ReadStmt(Stmt):
    name: str = ""
    def to_json(self) -> Dict[str, Any]:
        return {"type": "Read", "id": self.id, "name": self.name}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}Read#{self.id}({self.name})\n"

@dataclass
class Return(Stmt):
    expr: Optional[Expr] = None
    def to_json(self) -> Dict[str, Any]:
        obj = {"type": "Return", "id": self.id}
        if self.expr is not None: obj["expr"] = self.expr.to_json()
        return obj
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}Return#{self.id}\n"
        if self.expr: s += self.expr.pretty(indent + 1)
        return s

@dataclass
class FuncDef(Stmt):
    # для v1 параметры опционально пустые; функции могут возвращать значение (func) или быть процедурами (proc)
    name: str = ""
    is_proc: bool = True
    ret_type: Optional[TypeKind] = None    # только если is_proc == False
    body: Block = None
    params: List[str] = field(default_factory=list)  # упрощённо: только имена
    def to_json(self) -> Dict[str, Any]:
        obj = {"type": "FuncDef", "id": self.id, "name": self.name,
               "kind": "proc" if self.is_proc else "func",
               "params": self.params,
               "body": self.body.to_json()}
        if not self.is_proc and self.ret_type is not None:
            obj["ret_type"] = self.ret_type.name
        return obj
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        kind = "proc" if self.is_proc else f"func:{self.ret_type.name if self.ret_type else 'UNKNOWN'}"
        s = f"{pad}FuncDef#{self.id}({kind} {self.name})\n"
        for p in self.params:
            s += f"{pad}  param({p})\n"
        s += self.body.pretty(indent + 1)
        return s

# example log(x); → CallStmt("log", [Ident("x")])
@dataclass
class CallStmt(Stmt):
    name: str = ""
    args: List[Expr] = field(default_factory=list)
    def to_json(self) -> Dict[str, Any]:
        return {"type": "CallStmt", "id": self.id, "name": self.name,
                "args": [a.to_json() for a in self.args]}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}CallStmt#{self.id}({self.name})\n"
        for a in self.args: s += a.pretty(indent + 1)
        return s

# Верхний уровень

@dataclass
class Program(Node):
    stmts: List[Stmt] = field(default_factory=list)
    def to_json(self) -> Dict[str, Any]:
        return {"type": "Program", "id": self.id, "stmts": [s.to_json() for s in self.stmts]}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}Program#{self.id}\n"
        for st in self.stmts: s += st.pretty(indent + 1)
        return s
