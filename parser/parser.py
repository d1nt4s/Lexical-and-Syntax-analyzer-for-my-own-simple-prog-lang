from __future__ import annotations
from typing import List, Optional
from lexer.tokens import Token, TokenKind
from parser.ast import Program, ExprStmt, Expr, BinOp, UnOp, Literal, Ident, OpKind
from parser.errors import ParseError

class _TokenStream:
    def __init__(self, tokens: List[Token]) -> None:
        self.toks = tokens
        self.i = 0
        self.last_ok_line = 1
        self.last_ok_col = 1

    def at_end(self) -> bool:
        return self.peek().kind == TokenKind.EOF

    def peek(self) -> Token:
        if self.i < len(self.toks):
            return self.toks[self.i]
        return self.toks[-1]

    def prev(self) -> Token:
        if self.i == 0:
            return self.toks[0]
        return self.toks[self.i - 1]

    def advance(self) -> Token:
        tok = self.peek()
        if self.i < len(self.toks):
            self.i += 1
        # обновляем последнюю "безопасную" позицию — на предыдущем токене
        self.last_ok_line = tok.line
        self.last_ok_col = tok.col
        return tok

    def match(self, *kinds: TokenKind) -> Optional[Token]:
        if self.peek().kind in kinds:
            return self.advance()
        return None

    def expect(self, kind: TokenKind, msg: str) -> Token:
        tok = self.peek()
        if tok.kind != kind:
            raise ParseError(self.last_ok_line, self.last_ok_col, tok, msg)
        return self.advance()


# -------------------- Основной парсер --------------------

class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.ts = _TokenStream(tokens)

    def parse(self) -> Program:
        prog = Program()
        # Program = { expression-stmt }* EOF
        while not self.ts.at_end():
            expr = self.parse_expr()
            self.ts.expect(TokenKind.SEMI, "Expected ';' after expression")
            prog.stmts.append(ExprStmt(expr=expr))
        return prog

    # expr → or
    def parse_expr(self) -> Expr:
        return self.parse_or()

    # or → and ( "||" and )*
    def parse_or(self) -> Expr:
        left = self.parse_and()
        while self.ts.match(TokenKind.OR):
            op = OpKind.OR
            right = self.parse_and()
            left = BinOp(op=op, left=left, right=right)
        return left

    # and → equality ( "&&" equality )*
    def parse_and(self) -> Expr:
        left = self.parse_equality()
        while self.ts.match(TokenKind.AND):
            op = OpKind.AND
            right = self.parse_equality()
            left = BinOp(op=op, left=left, right=right)
        return left

    # equality → relational ( ( "==" | "!=" ) relational )*
    def parse_equality(self) -> Expr:
        left = self.parse_relational()
        while True:
            if self.ts.match(TokenKind.EQ):
                op = OpKind.EQ
            elif self.ts.match(TokenKind.NEQ):
                op = OpKind.NEQ
            else:
                break
            right = self.parse_relational()
            left = BinOp(op=op, left=left, right=right)
        return left

    # relational → add ( ( "<" | "<=" | ">" | ">=" ) add )*
    def parse_relational(self) -> Expr:
        left = self.parse_add()
        while True:
            if self.ts.match(TokenKind.LT):
                op = OpKind.LT
            elif self.ts.match(TokenKind.LE):
                op = OpKind.LE
            elif self.ts.match(TokenKind.GT):
                op = OpKind.GT
            elif self.ts.match(TokenKind.GE):
                op = OpKind.GE
            else:
                break
            right = self.parse_add()
            left = BinOp(op=op, left=left, right=right)
        return left

    # add → mul ( ( "+" | "-" ) mul )*
    def parse_add(self) -> Expr:
        left = self.parse_mul()
        while True:
            if self.ts.match(TokenKind.PLUS):
                op = OpKind.ADD
            elif self.ts.match(TokenKind.MINUS):
                op = OpKind.SUB
            else:
                break
            right = self.parse_mul()
            left = BinOp(op=op, left=left, right=right)
        return left

    # mul → unary ( ( "*" | "/" ) unary )*
    def parse_mul(self) -> Expr:
        left = self.parse_unary()
        while True:
            if self.ts.match(TokenKind.STAR):
                op = OpKind.MUL
            elif self.ts.match(TokenKind.SLASH):
                op = OpKind.DIV
            else:
                break
            right = self.parse_unary()
            left = BinOp(op=op, left=left, right=right)
        return left

    # unary → ( "!" | "-" ) unary | primary
    def parse_unary(self) -> Expr:
        if self.ts.match(TokenKind.NOT):
            op = OpKind.NOT
            operand = self.parse_unary()
            return UnOp(op=op, operand=operand)
        if self.ts.match(TokenKind.MINUS):
            op = OpKind.NEG
            operand = self.parse_unary()
            return UnOp(op=op, operand=operand)
        return self.parse_primary()

    # primary → INT | REAL | BOOL | IDENT | "(" expr ")"
    def parse_primary(self) -> Expr:
        tok = self.ts.peek()
        # литералы
        if tok.kind == TokenKind.INT:
            self.ts.advance()
            return Literal(value=tok.value, kind="int")
        if tok.kind == TokenKind.REAL:
            self.ts.advance()
            return Literal(value=tok.value, kind="real")
        if tok.kind == TokenKind.BOOL:
            self.ts.advance()
            return Literal(value=tok.value, kind="bool")
        # идентификаторы
        if tok.kind == TokenKind.IDENT:
            self.ts.advance()
            return Ident(name=tok.lexeme)
        # (expr)
        if self.ts.match(TokenKind.LPAREN):
            e = self.parse_expr()
            self.ts.expect(TokenKind.RPAREN, "Expected ')' after expression")
            return e

        # ничего не подошло — ошибка
        raise ParseError(self.ts.last_ok_line, self.ts.last_ok_col, tok, "Expected primary expression")


def parse(tokens: List[Token]) -> Program:
    return Parser(tokens).parse()
