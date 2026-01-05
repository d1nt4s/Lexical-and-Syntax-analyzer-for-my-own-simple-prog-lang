from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from enum import Enum, auto

# === Expressions (from Stage 3) ===

class OpKind(Enum):
    # binary
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
    # unary
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
    span: Optional[SourceSpan] = None
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        raise NotImplementedError
    
    def _get_type_str(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        """Get type string for this node, or empty string if no type."""
        if types_by_node_id is None:
            return ""
        typ = types_by_node_id.get(self.id)
        if typ is None:
            return ""
        return self._format_type(typ)
    
    def _format_type(self, typ: Any) -> str:
        """Format type for display. Override in subclasses if needed."""
        # Import here to avoid circular dependency
        from semantic.types import TypeTag, ArrayType, StructType
        if hasattr(typ, 'tag'):
            if typ.tag == TypeTag.INT:
                return ":int"
            elif typ.tag == TypeTag.REAL:
                return ":real"
            elif typ.tag == TypeTag.BOOL:
                return ":bool"
            elif typ.tag == TypeTag.VOID:
                return ":void"
            elif typ.tag == TypeTag.ARRAY:
                if isinstance(typ, ArrayType):
                    base_str = self._format_type(typ.elem).lstrip(':')
                    return f":{base_str}[{typ.dims}]"
            elif typ.tag == TypeTag.STRUCT:
                if isinstance(typ, StructType):
                    return f":struct {typ.name}"
        return ""

@dataclass(frozen=True)
class SourcePos:
    line: int
    col: int

@dataclass(frozen=True)
class SourceSpan:
    start: SourcePos
    end: SourcePos

# --- Exprs ---
class Expr(Node):
    pass

@dataclass
class BinOp(Expr):
    op: OpKind = OpKind.ADD
    left: Expr = None
    right: Expr = None
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        result = {"type": "BinOp", "id": self.id, "op": self.op.name,
                "left": self.left.to_json(types_by_node_id), "right": self.right.to_json(types_by_node_id)}
        type_str = self._get_type_str(types_by_node_id)
        if type_str:
            result["ty"] = type_str.lstrip(':')
        return result
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        type_str = self._get_type_str(types_by_node_id)
        return f"{pad}BinOp#{self.id}({self.op.name}){type_str}\n" + \
               self.left.pretty(indent + 1, types_by_node_id) + self.right.pretty(indent + 1, types_by_node_id)

@dataclass
class UnOp(Expr):
    op: OpKind = OpKind.NEG
    expr: Expr = None
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        result = {"type": "UnOp", "id": self.id, "op": self.op.name,
                "expr": self.expr.to_json(types_by_node_id)}
        type_str = self._get_type_str(types_by_node_id)
        if type_str:
            result["ty"] = type_str.lstrip(':')
        return result
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        type_str = self._get_type_str(types_by_node_id)
        return f"{pad}UnOp#{self.id}({self.op.name}){type_str}\n" + self.expr.pretty(indent + 1, types_by_node_id)

@dataclass
class Literal(Expr):
    value: Any = None
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        result = {"type": "Literal", "id": self.id, "value": self.value}
        type_str = self._get_type_str(types_by_node_id)
        if type_str:
            result["ty"] = type_str.lstrip(':')
        return result
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        type_str = self._get_type_str(types_by_node_id)
        return f"{pad}Literal#{self.id}({self.value!r}){type_str}\n"

@dataclass
class Ident(Expr):
    name: str = ""
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        result = {"type": "Ident", "id": self.id, "name": self.name}
        type_str = self._get_type_str(types_by_node_id)
        if type_str:
            result["ty"] = type_str.lstrip(':')
        return result
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        type_str = self._get_type_str(types_by_node_id)
        return f"{pad}Ident#{self.id}({self.name}){type_str}\n"

@dataclass
class IndexExpr(Expr):
    base: Expr = None
    index: Expr = None
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        result = {"type": "IndexExpr", "id": self.id, "base": self.base.to_json(types_by_node_id), "index": self.index.to_json(types_by_node_id)}
        type_str = self._get_type_str(types_by_node_id)
        if type_str:
            result["ty"] = type_str.lstrip(':')
        return result
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        type_str = self._get_type_str(types_by_node_id)
        return f"{pad}IndexExpr#{self.id}{type_str}\n" + self.base.pretty(indent + 1, types_by_node_id) + self.index.pretty(indent + 1, types_by_node_id)

@dataclass
class CallExpr(Expr):
    callee: str = ""
    args: List[Expr] = field(default_factory=list)
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        result = {"type": "CallExpr", "id": self.id, "callee": self.callee, "args": [a.to_json(types_by_node_id) for a in self.args]}
        type_str = self._get_type_str(types_by_node_id)
        if type_str:
            result["ty"] = type_str.lstrip(':')
        return result
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        type_str = self._get_type_str(types_by_node_id)
        s = f"{pad}CallExpr#{self.id}({self.callee}){type_str}\n"
        for a in self.args:
            s += a.pretty(indent + 1, types_by_node_id)
        return s

@dataclass
class FieldAccessExpr(Expr):
    base: Expr = None
    field: str = ""
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        result = {"type": "FieldAccessExpr", "id": self.id, "base": self.base.to_json(types_by_node_id), "field": self.field}
        type_str = self._get_type_str(types_by_node_id)
        if type_str:
            result["ty"] = type_str.lstrip(':')
        return result
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        type_str = self._get_type_str(types_by_node_id)
        return f"{pad}FieldAccessExpr#{self.id}({self.field}){type_str}\n" + self.base.pretty(indent + 1, types_by_node_id)

# === Statements and top level (Stage 4) ===

class TypeKind(Enum):
    INT = auto()
    REAL = auto()
    BOOL = auto()

@dataclass
class CastExpr(Expr):
    target_type: TypeKind = TypeKind.INT  # INT or REAL
    expr: Expr = None
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        result = {"type": "CastExpr", "id": self.id, "target_type": self.target_type.name, "expr": self.expr.to_json(types_by_node_id)}
        type_str = self._get_type_str(types_by_node_id)
        if type_str:
            result["ty"] = type_str.lstrip(':')
        return result
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        type_str = self._get_type_str(types_by_node_id)
        return f"{pad}CastExpr#{self.id}({self.target_type.name}){type_str}\n" + self.expr.pretty(indent + 1, types_by_node_id)

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
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        return {"type": "StructDecl", "id": self.id, "name": self.name, "fields": [f.to_json() for f in self.fields]}
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        s = f"{pad}StructDecl#{self.id}({self.name})\n"
        for f in self.fields:
            s += f.pretty(indent + 1)
        return s

@dataclass
class ExprStmt(Stmt):
    expr: Expr = None
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        return {"type": "ExprStmt", "id": self.id, "expr": self.expr.to_json(types_by_node_id)}
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        return f"{pad}ExprStmt#{self.id}\n" + self.expr.pretty(indent + 1, types_by_node_id)

@dataclass
class Block(Stmt):
    stmts: List[Stmt] = field(default_factory=list)
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        return {"type": "Block", "id": self.id, "stmts": [s.to_json(types_by_node_id) for s in self.stmts]}
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        s = f"{pad}Block#{self.id}\n"
        for st in self.stmts: s += st.pretty(indent + 1, types_by_node_id)
        return s

@dataclass
class Decl(Stmt):
    type_spec: TypeSpec = None
    name: str = ""
    init: Optional[Expr] = None
    @property
    def type(self) -> TypeKind:
        """Backward compatibility: returns TypeKind from type_spec"""
        if isinstance(self.type_spec, BaseType):
            return self.type_spec.kind
        elif isinstance(self.type_spec, ArrayType):
            # For arrays, return base type
            base = self.type_spec.base
            while isinstance(base, ArrayType):
                base = base.base
            if isinstance(base, BaseType):
                return base.kind
        return TypeKind.INT  # fallback
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        obj = {"type": "Decl", "id": self.id, "type_spec": self.type_spec.to_json() if self.type_spec else None, "name": self.name}
        if self.init is not None: obj["init"] = self.init.to_json(types_by_node_id)
        return obj
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        type_str = self.type_spec.pretty(0).strip() if self.type_spec else "UNKNOWN"
        s = f"{pad}Decl#{self.id}({type_str} {self.name})\n"
        if self.init: s += self.init.pretty(indent + 1, types_by_node_id)
        return s

@dataclass
class Assign(Stmt):
    lvalue: Expr = None  # Ident or IndexExpr
    expr: Expr = None
    @property
    def name(self) -> str:
        """Backward compatibility: returns name from lvalue if it's Ident"""
        if isinstance(self.lvalue, Ident):
            return self.lvalue.name
        return ""
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        return {"type": "Assign", "id": self.id, "lvalue": self.lvalue.to_json(types_by_node_id), "expr": self.expr.to_json(types_by_node_id)}
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        return f"{pad}Assign#{self.id}\n" + self.lvalue.pretty(indent + 1, types_by_node_id) + self.expr.pretty(indent + 1, types_by_node_id)

@dataclass
class If(Stmt):
    cond: Expr = None
    then_branch: Stmt = None
    else_branch: Optional[Stmt] = None
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        obj = {"type": "If", "id": self.id,
               "cond": self.cond.to_json(types_by_node_id),
               "then": self.then_branch.to_json(types_by_node_id)}
        if self.else_branch is not None: obj["else"] = self.else_branch.to_json(types_by_node_id)
        return obj
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        s = f"{pad}If#{self.id}\n" + self.cond.pretty(indent + 1, types_by_node_id) + self.then_branch.pretty(indent + 1, types_by_node_id)
        if self.else_branch: s += self.else_branch.pretty(indent + 1, types_by_node_id)
        return s

@dataclass
class For(Stmt):
    init: Stmt = None          # Decl | Assign
    cond: Optional[Expr] = None
    step: Optional[Assign] = None
    body: Stmt = None
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        obj = {"type": "For", "id": self.id,
               "init": self.init.to_json(types_by_node_id),
               "body": self.body.to_json(types_by_node_id)}
        if self.cond is not None: obj["cond"] = self.cond.to_json(types_by_node_id)
        if self.step is not None: obj["step"] = self.step.to_json(types_by_node_id)
        return obj
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        s = f"{pad}For#{self.id}\n"
        s += self.init.pretty(indent + 1, types_by_node_id)
        if self.cond: s += self.cond.pretty(indent + 1, types_by_node_id)
        if self.step: s += self.step.pretty(indent + 1, types_by_node_id)
        s += self.body.pretty(indent + 1, types_by_node_id)
        return s

@dataclass
class PrintStmt(Stmt):
    expr: Expr = None
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        return {"type": "Print", "id": self.id, "expr": self.expr.to_json(types_by_node_id)}
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        return f"{pad}Print#{self.id}\n" + self.expr.pretty(indent + 1, types_by_node_id)

@dataclass
class ReadStmt(Stmt):
    name: str = ""
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        return {"type": "Read", "id": self.id, "name": self.name}
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        return f"{pad}Read#{self.id}({self.name})\n"

@dataclass
class Return(Stmt):
    expr: Optional[Expr] = None
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        obj = {"type": "Return", "id": self.id}
        if self.expr is not None: obj["expr"] = self.expr.to_json(types_by_node_id)
        return obj
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        s = f"{pad}Return#{self.id}\n"
        if self.expr: s += self.expr.pretty(indent + 1, types_by_node_id)
        return s

@dataclass
class FuncDef(Stmt):
    # functions can return value (func) or be procedures (proc)
    name: str = ""
    is_proc: bool = True
    ret_type: Optional[TypeSpec] = None    # only if is_proc == False
    body: Block = None
    params: List[Param] = field(default_factory=list)  # typed parameters
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        obj = {"type": "FuncDef", "id": self.id, "name": self.name,
               "kind": "proc" if self.is_proc else "func",
               "params": [p.to_json() for p in self.params],
               "body": self.body.to_json(types_by_node_id)}
        if not self.is_proc and self.ret_type is not None:
            obj["ret_type"] = self.ret_type.to_json()
        return obj
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        if self.is_proc:
            kind = "proc"
        else:
            type_str = self.ret_type.pretty(0).strip() if self.ret_type else "UNKNOWN"
            kind = f"func:{type_str}"
        s = f"{pad}FuncDef#{self.id}({kind} {self.name})\n"
        for p in self.params:
            s += p.pretty(indent + 1)
        s += self.body.pretty(indent + 1, types_by_node_id)
        return s

# example log(x); → CallStmt("log", [Ident("x")])
@dataclass
class CallStmt(Stmt):
    name: str = ""
    args: List[Expr] = field(default_factory=list)
    def to_json(self, types_by_node_id: Optional[Dict[int, Any]] = None) -> Dict[str, Any]:
        return {"type": "CallStmt", "id": self.id, "name": self.name,
                "args": [a.to_json(types_by_node_id) for a in self.args]}
    def pretty(self, indent: int = 0, types_by_node_id: Optional[Dict[int, Any]] = None) -> str:
        pad = "  " * indent
        s = f"{pad}CallStmt#{self.id}({self.name})\n"
        for a in self.args: s += a.pretty(indent + 1, types_by_node_id)
        return s

# Top level

@dataclass
class Program(Node):
    stmts: List[Stmt] = field(default_factory=list)
    types_by_node_id: Optional[Dict[int, Any]] = None  # node.id -> Type (set after semantic analysis)
    def to_json(self) -> Dict[str, Any]:
        return {"type": "Program", "id": self.id, "stmts": [s.to_json(self.types_by_node_id) for s in self.stmts]}
    def pretty(self, indent: int = 0) -> str:
        pad = "  " * indent
        s = f"{pad}Program#{self.id}\n"
        for st in self.stmts: s += st.pretty(indent + 1, self.types_by_node_id)
        return s
