"""
5) Примеры
Добавь минимум 2 новых semantic error примера:
- type mismatch int + real без кастования (должно падать)
- неверный cast real->int (например int(1.2))
И один ok пример с разрешённым cast real->int где дробная часть .0 (например int(3.0)).Intermediate Representation (IR) for stack machine.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Union, Any, Optional
from enum import Enum


class IROp(Enum):
    """Stack machine operations."""
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
    EQ = "eq"
    NEQ = "neq"
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class IRInstruction:
    """Base IR instruction."""
    pass


@dataclass
class Push(IRInstruction):
    """Push value or variable onto stack. For variables, use push <name>."""
    value: Union[int, float, bool, str]
    
    def __str__(self) -> str:
        if isinstance(self.value, bool):
            return f"push {'true' if self.value else 'false'}"
        return f"push {self.value}"


@dataclass
class Op(IRInstruction):
    """Stack machine operation."""
    op: IROp
    
    def __str__(self) -> str:
        return self.op.value


@dataclass
class Label(IRInstruction):
    """Label for jumps."""
    name: str
    
    def __str__(self) -> str:
        return f"label {self.name}"


@dataclass
class Jmp(IRInstruction):
    """Unconditional jump to label."""
    label: str
    
    def __str__(self) -> str:
        return f"jmp {self.label}"


@dataclass
class JmpIfFalse(IRInstruction):
    """Conditional jump: if false on stack, jump to label. Consumes bool from stack."""
    label: str
    
    def __str__(self) -> str:
        return f"jmp_if_false {self.label}"


@dataclass
class Pop(IRInstruction):
    """Remove top value from stack. With operand: pop <name> stores value to variable."""
    name: Optional[str] = None  # If provided, stores value to variable before popping
    
    def __str__(self) -> str:
        if self.name is not None:
            return f"pop {self.name}"
        return "pop"


@dataclass
class Store(IRInstruction):
    """Store value to variable. Consumes value from stack."""
    name: str
    
    def __str__(self) -> str:
        return f"store {self.name}"


@dataclass
class Load(IRInstruction):
    """Load variable value onto stack."""
    name: str
    
    def __str__(self) -> str:
        return f"load {self.name}"


@dataclass
class StoreIndex(IRInstruction):
    """Store value to array element. Stack: [value, base, index] -> []"""
    
    def __str__(self) -> str:
        return "store_index"


@dataclass
class LoadIndex(IRInstruction):
    """Load array element onto stack. Stack: [base, index] -> [value]"""
    
    def __str__(self) -> str:
        return "load_index"


@dataclass
class StoreField(IRInstruction):
    """Store value to struct field. Stack: [value, base] -> []"""
    field: str
    
    def __str__(self) -> str:
        return f"store_field {self.field}"


@dataclass
class LoadField(IRInstruction):
    """Load struct field onto stack. Stack: [base] -> [value]"""
    field: str
    
    def __str__(self) -> str:
        return f"load_field {self.field}"


@dataclass
class Call(IRInstruction):
    """Call function. Arguments must be on stack left-to-right."""
    name: str
    
    def __str__(self) -> str:
        return f"call {self.name}"


@dataclass
class Ret(IRInstruction):
    """Return from procedure (proc). No return value."""
    
    def __str__(self) -> str:
        return "ret"


@dataclass
class Retv(IRInstruction):
    """Return from function (func) with value. Consumes value from stack."""
    
    def __str__(self) -> str:
        return "retv"


IRProgram = List[IRInstruction]


def ir_to_string(program: IRProgram) -> str:
    """Convert IR program to string."""
    return "\n".join(str(instr) for instr in program)

