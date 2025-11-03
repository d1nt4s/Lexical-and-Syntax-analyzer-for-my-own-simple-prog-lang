from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Position:
    line: int
    column: int

@dataclass(frozen=True)
class Token:
    kind: str
    lexeme: str
    pos: Position
    value: Any | None = None