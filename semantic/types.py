from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto

class TypeTag(Enum):
    INT = auto()
    REAL = auto()
    BOOL = auto()
    ARRAY = auto()
    STRUCT = auto()
    VOID = auto()

@dataclass(frozen=True)
class Type:
    tag: TypeTag

INT  = Type(TypeTag.INT)
REAL = Type(TypeTag.REAL)
BOOL = Type(TypeTag.BOOL)
VOID = Type(TypeTag.VOID)

@dataclass(frozen=True)
class ArrayType(Type):
    elem: Type
    dims: int = 1
    def __init__(self, elem: Type, dims: int = 1):
        object.__setattr__(self, "tag", TypeTag.ARRAY)
        object.__setattr__(self, "elem", elem)
        object.__setattr__(self, "dims", dims)

@dataclass(frozen=True)
class StructType(Type):
    name: str
    def __init__(self, name: str):
        object.__setattr__(self, "tag", TypeTag.STRUCT)
        object.__setattr__(self, "name", name)