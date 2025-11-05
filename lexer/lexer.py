from __future__ import annotations
from typing import List
from .tokens import Token, TokenKind, KEYWORDS
from .errors import LexError


class Lexer:
    def __init__(self, source: str) -> None:
        self.src = source
        self.n = len(source)
        self.i = 0
        self.line = 1
        self.col = 1

    # ------------- core scanning helpers -------------
    def at_end(self) -> bool:
        return self.i >= self.n

    def peek(self) -> str:
        return "\0" if self.at_end() else self.src[self.i]

    def peek_next(self) -> str:
        j = self.i + 1
        return "\0" if j >= self.n else self.src[j]

    def advance(self) -> str:
        if self.at_end():
            return "\0"
        ch = self.src[self.i]
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.at_end() or self.src[self.i] != expected:
            return False
        self.advance()
        return True

    def make(self, kind: TokenKind, lexeme: str, line: int, col: int, value=None) -> Token:
        return Token(kind, lexeme, line, col, value)

    # ------------- skipping -------------
    def skip_ws_and_comments(self) -> None:
        while True:
            ch = self.peek()
            # whitespace
            if ch in " \r\t\n":
                self.advance()
                continue
            # line comment // ... EOL
            if ch == "/" and self.peek_next() == "/":
                while self.peek() not in ("\n", "\0"):
                    self.advance()
                continue
            # block comment /* ... */
            if ch == "/" and self.peek_next() == "*":
                start_line, start_col = self.line, self.col
                self.advance()  # '/'
                self.advance()  # '*'
                while True:
                    if self.at_end():
                        raise LexError("Unterminated block comment (expected '*/')", start_line, start_col)
                    if self.peek() == "*" and self.peek_next() == "/":
                        self.advance()  # '*'
                        self.advance()  # '/'
                        break
                    else:
                        self.advance()
                continue
            break

    # ------------- scanners -------------
    def scan_identifier_or_keyword(self) -> Token:
        start_i, start_line, start_col = self.i, self.line, self.col
        self.advance()  # first char is [A-Za-z_]
        while True:
            ch = self.peek()
            if ch.isalnum() or ch == "_":
                self.advance()
            else:
                break
        lexeme = self.src[start_i:self.i]
        kind = KEYWORDS.get(lexeme)
        if kind is None:
            return self.make(TokenKind.IDENT, lexeme, start_line, start_col)
        # handle bool literals
        if kind == TokenKind.BOOL:
            val = (lexeme == "true")
            return self.make(TokenKind.BOOL, lexeme, start_line, start_col, val)
        return self.make(kind, lexeme, start_line, start_col)

    def scan_number(self) -> Token:
        start_i, start_line, start_col = self.i, self.line, self.col
        while self.peek().isdigit():
            self.advance()
        is_real = False
        if self.peek() == "." and self.peek_next().isdigit():
            is_real = True
            self.advance()
            while self.peek().isdigit():
                self.advance()
        lexeme = self.src[start_i:self.i]
        if is_real:
            return self.make(TokenKind.REAL, lexeme, start_line, start_col, float(lexeme))
        else:
            return self.make(TokenKind.INT, lexeme, start_line, start_col, int(lexeme))

    # ------------- public API -------------
    def scan_all(self) -> List[Token]:
        tokens: List[Token] = []
        while True:
            self.skip_ws_and_comments()
            start_line, start_col = self.line, self.col
            ch = self.peek()
            if ch == "\0":
                tokens.append(self.make(TokenKind.EOF, "", start_line, start_col))
                return tokens

            # identifiers / keywords
            if ch.isalpha() or ch == "_":
                tokens.append(self.scan_identifier_or_keyword())
                continue

            # numbers
            if ch.isdigit():
                tokens.append(self.scan_number())
                continue

            # two-char operators
            if ch == "=" and self.peek_next() == "=":
                self.advance(); self.advance()
                tokens.append(self.make(TokenKind.EQ, "==", start_line, start_col))
                continue
            if ch == "!" and self.peek_next() == "=":
                self.advance(); self.advance()
                tokens.append(self.make(TokenKind.NEQ, "!=", start_line, start_col))
                continue
            if ch == "<" and self.peek_next() == "=":
                self.advance(); self.advance()
                tokens.append(self.make(TokenKind.LE, "<=", start_line, start_col))
                continue
            if ch == ">" and self.peek_next() == "=":
                self.advance(); self.advance()
                tokens.append(self.make(TokenKind.GE, ">=", start_line, start_col))
                continue
            if ch == "&" and self.peek_next() == "&":
                self.advance(); self.advance()
                tokens.append(self.make(TokenKind.AND, "&&", start_line, start_col))
                continue
            if ch == "|" and self.peek_next() == "|":
                self.advance(); self.advance()
                tokens.append(self.make(TokenKind.OR, "||", start_line, start_col))
                continue

            # single-char tokens
            ch = self.advance()
            single = {
                ';': TokenKind.SEMI,
                ',': TokenKind.COMMA,
                '(': TokenKind.LPAREN,
                ')': TokenKind.RPAREN,
                '{': TokenKind.LBRACE,
                '}': TokenKind.RBRACE,
                '[': TokenKind.LBRACKET,
                ']': TokenKind.RBRACKET,
                '+': TokenKind.PLUS,
                '-': TokenKind.MINUS,
                '*': TokenKind.STAR,
                '/': TokenKind.SLASH,
                '=': TokenKind.ASSIGN,
                '<': TokenKind.LT,
                '>': TokenKind.GT,
                '!': TokenKind.NOT,
            }
            kind = single.get(ch)
            if kind is None:
                if ch == '.':
                    # Проверяем, не является ли это частью числа (например, 1.5)
                    # Если следующий символ цифра, это ошибка - числа должны быть в формате d+.d+
                    if self.peek().isdigit():
                        raise LexError("Unexpected '.' (reals must be like d+.d+)", start_line, start_col)
                    # Иначе это токен точки для доступа к полю
                    tokens.append(self.make(TokenKind.DOT, ch, start_line, start_col))
                    continue
                raise LexError(f"Unknown character '{ch}'", start_line, start_col)
            tokens.append(self.make(kind, ch, start_line, start_col))
