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

@dataclass
class IndexExpr(Expr):
    base: Expr = None
    index: Expr = None
    def to_json(self) -> Dict[str, Any]:
        return {"type": "IndexExpr", "id": self.id, "base": self.base.to_json(), "index": self.index.to_json()}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}IndexExpr#{self.id}\n" + self.base.pretty(indent + 1) + self.index.pretty(indent + 1)

@dataclass
class CallExpr(Expr):
    callee: str = ""
    args: List[Expr] = field(default_factory=list)
    def to_json(self) -> Dict[str, Any]:
        return {"type": "CallExpr", "id": self.id, "callee": self.callee, "args": [a.to_json() for a in self.args]}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}CallExpr#{self.id}({self.callee})\n"
        for a in self.args:
            s += a.pretty(indent + 1)
        return s

@dataclass
class FieldAccessExpr(Expr):
    base: Expr = None
    field: str = ""
    def to_json(self) -> Dict[str, Any]:
        return {"type": "FieldAccessExpr", "id": self.id, "base": self.base.to_json(), "field": self.field}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}FieldAccessExpr#{self.id}({self.field})\n" + self.base.pretty(indent + 1)

# === Операторы и верхний уровень (Этап 4) ===

class TypeKind(Enum):
    INT = auto()
    REAL = auto()
    BOOL = auto()

# --- Type specifications ---
class TypeSpec(Node):
    """Base class for type specifications."""
    pass

@dataclass
class Param(Node):
    type_spec: TypeSpec = None
    name: str = ""
    def to_json(self) -> Dict[str, Any]:
        return {"type": "Param", "id": self.id, "type_spec": self.type_spec.to_json(), "name": self.name}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        type_str = self.type_spec.pretty(0).strip() if self.type_spec else "UNKNOWN"
        return f"{pad}Param#{self.id}({type_str} {self.name})\n"

@dataclass
class BaseType(TypeSpec):
    kind: TypeKind = TypeKind.INT
    def to_json(self) -> Dict[str, Any]:
        return {"type": "BaseType", "id": self.id, "kind": self.kind.name}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}BaseType#{self.id}({self.kind.name})\n"

@dataclass
class ArrayType(TypeSpec):
    base: TypeSpec = None
    dims: int = 1
    def to_json(self) -> Dict[str, Any]:
        return {"type": "ArrayType", "id": self.id, "base": self.base.to_json(), "dims": self.dims}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}ArrayType#{self.id}(dims={self.dims})\n" + self.base.pretty(indent + 1)

@dataclass
class NamedStructType(TypeSpec):
    """Nominal struct type: struct Name"""
    name: str = ""
    def to_json(self) -> Dict[str, Any]:
        return {"type": "NamedStructType", "id": self.id, "name": self.name}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}NamedStructType#{self.id}({self.name})\n"

class Stmt(Node):
    pass

@dataclass
class FieldDecl(Node):
    type_spec: TypeSpec = None
    name: str = ""
    def to_json(self) -> Dict[str, Any]:
        return {"type": "FieldDecl", "id": self.id, "type_spec": self.type_spec.to_json(), "name": self.name}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        type_str = self.type_spec.pretty(0).strip() if self.type_spec else "UNKNOWN"
        return f"{pad}FieldDecl#{self.id}({type_str} {self.name})\n"

@dataclass
class EnumDecl(Stmt):
    name: str = ""
    members: List[str] = field(default_factory=list)
    def to_json(self) -> Dict[str, Any]:
        return {"type": "EnumDecl", "id": self.id, "name": self.name, "members": self.members}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        members_str = ", ".join(self.members)
        return f"{pad}EnumDecl#{self.id}({self.name} {{ {members_str} }})\n"

@dataclass
class StructDecl(Stmt):
    name: str = ""
    fields: List[FieldDecl] = field(default_factory=list)
    def to_json(self) -> Dict[str, Any]:
        return {"type": "StructDecl", "id": self.id, "name": self.name, "fields": [f.to_json() for f in self.fields]}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}StructDecl#{self.id}({self.name})\n"
        for f in self.fields:
            s += f.pretty(indent + 1)
        return s

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
    type_spec: TypeSpec = None
    name: str = ""
    init: Optional[Expr] = None
    @property
    def type(self) -> TypeKind:
        """Обратная совместимость: возвращает TypeKind из type_spec"""
        if isinstance(self.type_spec, BaseType):
            return self.type_spec.kind
        elif isinstance(self.type_spec, ArrayType):
            # Для массивов возвращаем базовый тип
            base = self.type_spec.base
            while isinstance(base, ArrayType):
                base = base.base
            if isinstance(base, BaseType):
                return base.kind
        return TypeKind.INT  # fallback
    def to_json(self) -> Dict[str, Any]:
        obj = {"type": "Decl", "id": self.id, "type_spec": self.type_spec.to_json(), "name": self.name}
        if self.init is not None: obj["init"] = self.init.to_json()
        return obj
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        type_str = self.type_spec.pretty(0).strip() if self.type_spec else "UNKNOWN"
        s = f"{pad}Decl#{self.id}({type_str} {self.name})\n"
        if self.init: s += self.init.pretty(indent + 1)
        return s

@dataclass
class Assign(Stmt):
    lvalue: Expr = None  # Ident or IndexExpr
    expr: Expr = None
    @property
    def name(self) -> str:
        """Обратная совместимость: возвращает имя из lvalue если это Ident"""
        if isinstance(self.lvalue, Ident):
            return self.lvalue.name
        return ""
    def to_json(self) -> Dict[str, Any]:
        return {"type": "Assign", "id": self.id, "lvalue": self.lvalue.to_json(), "expr": self.expr.to_json()}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        return f"{pad}Assign#{self.id}\n" + self.lvalue.pretty(indent + 1) + self.expr.pretty(indent + 1)

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
    # функции могут возвращать значение (func) или быть процедурами (proc)
    name: str = ""
    is_proc: bool = True
    ret_type: Optional[TypeSpec] = None    # только если is_proc == False
    body: Block = None
    params: List[Param] = field(default_factory=list)  # типизированные параметры
    def to_json(self) -> Dict[str, Any]:
        obj = {"type": "FuncDef", "id": self.id, "name": self.name,
               "kind": "proc" if self.is_proc else "func",
               "params": [p.to_json() for p in self.params],
               "body": self.body.to_json()}
        if not self.is_proc and self.ret_type is not None:
            obj["ret_type"] = self.ret_type.to_json()
        return obj
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        if self.is_proc:
            kind = "proc"
        else:
            type_str = self.ret_type.pretty(0).strip() if self.ret_type else "UNKNOWN"
            kind = f"func:{type_str}"
        s = f"{pad}FuncDef#{self.id}({kind} {self.name})\n"
        for p in self.params:
            s += p.pretty(indent + 1)
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
