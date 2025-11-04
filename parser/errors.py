from __future__ import annotations
from dataclasses import dataclass
from lexer.tokens import Token

@dataclass
class ParseError(Exception):
    last_ok_line: int
    last_ok_col: int
    at: Token
    message: str

    def __str__(self) -> str:
        return (
            f"ParseError near {self.at.line}:{self.at.col} "
            f"(after {self.last_ok_line}:{self.last_ok_col}): {self.message}"
        )
