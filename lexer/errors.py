from __future__ import annotations
from dataclasses import dataclass


@dataclass
class LexError(Exception):
    message: str
    line: int
    col: int

    def __str__(self) -> str:
        return f"LexError at {self.line}:{self.col}: {self.message}"