from .lexer import Lexer
from .tokens import Token, TokenKind
from .errors import LexError

def scan_all(src: str):
    """Convenience function to scan entire string into token list."""
    return Lexer(src).scan_all()

__all__ = ["Lexer", "Token", "TokenKind", "LexError", "scan_all"]
