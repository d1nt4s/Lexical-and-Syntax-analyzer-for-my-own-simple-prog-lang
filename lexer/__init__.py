from .lexer import Lexer
from .tokens import Token, TokenKind
from .errors import LexError

def scan_all(src: str):
    """Удобная функция для сканирования всей строки в список токенов."""
    return Lexer(src).scan_all()

__all__ = ["Lexer", "Token", "TokenKind", "LexError", "scan_all"]
