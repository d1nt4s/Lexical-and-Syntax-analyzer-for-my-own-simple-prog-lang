from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


class TokenKind(Enum):
    # Literals & identifiers
    IDENT = auto()
    INT = auto()
    REAL = auto()
    BOOL = auto()

    # Keywords (keep as distinct kinds for clarity in parser)
    KW_INT = auto()
    KW_REAL = auto()
    KW_BOOL = auto()
    KW_IF = auto()
    KW_ELSE = auto()
    KW_FOR = auto()
    KW_RETURN = auto()
    KW_READ = auto()
    KW_PRINT = auto()
    KW_FUNC = auto()
    KW_PROC = auto()

    # Delimiters
    SEMI = auto() # ;
    COMMA = auto() # ,
    LPAREN = auto() # (
    RPAREN = auto() # )
    LBRACE = auto() # {
    RBRACE = auto() # }
    LBRACKET = auto() # [
    RBRACKET = auto() # ]

    # Operators
    PLUS = auto() # +
    MINUS = auto() # -
    STAR = auto() # *
    SLASH = auto() # /
    ASSIGN = auto() # =
    EQ = auto() # ==
    NEQ = auto() # !=
    LT = auto() # <
    LE = auto() # <=
    GT = auto() # >
    GE = auto() # >=
    AND = auto() # &&
    OR = auto() # ||
    NOT = auto() # !

    EOF = auto()


KEYWORDS = {
    "int": TokenKind.KW_INT,
    "real": TokenKind.KW_REAL,
    "bool": TokenKind.KW_BOOL,
    "if": TokenKind.KW_IF,
    "else": TokenKind.KW_ELSE,
    "for": TokenKind.KW_FOR, # simplified for-loop in spec
    "return": TokenKind.KW_RETURN,
    "read": TokenKind.KW_READ,
    "print": TokenKind.KW_PRINT,
    "true": TokenKind.BOOL,
    "false": TokenKind.BOOL,
}


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    line: int
    col: int
    value: Optional[Any] = None # parsed literal value if any

    def __repr__(self) -> str:
        base = f"{self.kind.name}('{self.lexeme}')@{self.line}:{self.col}"
        if self.value is not None:
            return base + f"={self.value!r}"
        return base