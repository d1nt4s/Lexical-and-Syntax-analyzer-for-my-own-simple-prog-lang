from __future__ import annotations
from typing import List, Optional
from lexer.tokens import Token, TokenKind
from parser.ast import (
    Program, Stmt, Block, Decl, Assign, If, For, FuncDef, CallStmt,
    PrintStmt, ReadStmt, Return, ExprStmt,
    Expr, BinOp, UnOp, Literal, Ident, OpKind, TypeKind
)
from parser.errors import ParseError

# Короткое имя для удобства — поправьте здесь, если ваши имена в TokenKind отличаются
class K:  # noqa: N801
    INT = TokenKind.KW_INT
    REAL = TokenKind.KW_REAL
    BOOL = TokenKind.KW_BOOL
    IF = TokenKind.KW_IF
    ELSE = TokenKind.KW_ELSE
    FOR = TokenKind.KW_FOR
    FUNC = TokenKind.KW_FUNC
    PROC = TokenKind.KW_PROC
    RETURN = TokenKind.KW_RETURN
    READ = TokenKind.KW_READ
    PRINT = TokenKind.KW_PRINT
    IDENT = TokenKind.IDENT
    INT_LIT = TokenKind.INT
    REAL_LIT = TokenKind.REAL
    BOOL_LIT = TokenKind.BOOL
    ASSIGN = TokenKind.ASSIGN
    LPAREN = TokenKind.LPAREN
    RPAREN = TokenKind.RPAREN
    LBRACE = TokenKind.LBRACE
    RBRACE = TokenKind.RBRACE
    COMMA = TokenKind.COMMA
    SEMI = TokenKind.SEMI
    EOF = TokenKind.EOF
    # операторы для выражений/унараных уже поддерживаются Этапом 3:
    PLUS = TokenKind.PLUS
    MINUS = TokenKind.MINUS
    STAR = TokenKind.STAR
    SLASH = TokenKind.SLASH
    OR = TokenKind.OR
    AND = TokenKind.AND
    EQ = TokenKind.EQ
    NEQ = TokenKind.NEQ
    LT = TokenKind.LT
    LE = TokenKind.LE
    GT = TokenKind.GT
    GE = TokenKind.GE
    NOT = TokenKind.NOT

# === Внутренний поток токенов с запоминанием last_ok ===
class _TokenStream:
    def __init__(self, tokens: List[Token]) -> None:
        self.toks = tokens
        self.i = 0
        self.last_ok_line = 1
        self.last_ok_col = 1

    def peek(self) -> Token:
        return self.toks[self.i]

    def at_end(self) -> bool:
        return self.peek().kind == K.EOF

    def advance(self) -> Token:
        t = self.peek()
        self.i += 1
        # обновим last_ok только когда продвинулись успешно
        self.last_ok_line = t.line
        self.last_ok_col = t.col
        return t

    def match(self, *kinds: TokenKind) -> bool:
        if self.peek().kind in kinds:
            self.advance()
            return True
        return False

    def expect(self, kind: TokenKind, msg: str) -> Token:
        if self.peek().kind != kind:
            tok = self.peek()
            raise ParseError(self.last_ok_line, self.last_ok_col, tok, msg)
        return self.advance()

# === Парсер ===

class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.ts = _TokenStream(tokens)

    def parse(self) -> Program:
        stmts: List[Stmt] = []
        while not self.ts.at_end():
            # пустые ; разрешим — просто пропустим
            if self.ts.match(K.SEMI):
                continue
            stmts.append(self.parse_stmt())
        return Program(stmts=stmts)

    # --- Statements ---

    def parse_stmt(self) -> Stmt:
        tok = self.ts.peek()

        # блок
        if tok.kind == K.LBRACE:
            return self.parse_block()
        # if
        if tok.kind == K.IF:
            return self.parse_if()
        # for
        if tok.kind == K.FOR:
            return self.parse_for()
        # func/proc
        if tok.kind in (K.FUNC, K.PROC):
            return self.parse_funcdef()
        # return
        if tok.kind == K.RETURN:
            return self.parse_return()
        # read/print
        if tok.kind == K.READ:
            return self.parse_read()
        if tok.kind == K.PRINT:
            return self.parse_print()
        # объявления типов
        if tok.kind in (K.INT, K.REAL, K.BOOL):
            return self.parse_decl_stmt()
        # присваивание или вызов/expr;
        # Разрешаем начинать с унарных операторов, чтобы получить более точные сообщения об ошибках
        if tok.kind in (K.IDENT, K.LPAREN, K.MINUS, K.NOT, K.PLUS, K.INT_LIT, K.REAL_LIT, K.BOOL_LIT):
            # попытка присваивания: IDENT '=' expr ';'
            if tok.kind == K.IDENT:
                # заглянем на следующий токен — если '=', то это Assign
                name_tok = self.ts.advance()
                if self.ts.match(K.ASSIGN):
                    expr = self.parse_expr()
                    self.ts.expect(K.SEMI, "Expected ';' after assignment")
                    return Assign(name=name_tok.lexeme, expr=expr)
                # иначе откатываться не будем — будем считать это началом выражения/вызова
                # восстановим позицию на IDENT для parse_expr: просто создадим искусственный Ident из уже съеденного
                # проще: вернёмся на шаг
                self.ts.i -= 1  # безопасно, мы знаем что i>0
            # expression-statement (включая вызовы)
            expr = self.parse_expr()
            self.ts.expect(K.SEMI, "Expected ';' after expression")
            return ExprStmt(expr=expr)

        # ничего не подошло
        raise ParseError(self.ts.last_ok_line, self.ts.last_ok_col, tok, "Expected statement")

    def parse_block(self) -> Block:
        self.ts.expect(K.LBRACE, "Expected '{' to start block")
        stmts: List[Stmt] = []
        while not self.ts.at_end() and self.ts.peek().kind != K.RBRACE:
            if self.ts.match(K.SEMI):  # разрешим пустые строки
                continue
            stmts.append(self.parse_stmt())
        self.ts.expect(K.RBRACE, "Expected '}' to end block")
        return Block(stmts=stmts)

    def parse_if(self) -> If:
        self.ts.expect(K.IF, "Expected 'if'")
        self.ts.expect(K.LPAREN, "Expected '(' after 'if'")
        cond = self.parse_expr()
        self.ts.expect(K.RPAREN, "Expected ')' after condition")
        then_branch = self.parse_stmt()
        else_branch: Optional[Stmt] = None
        if self.ts.match(K.ELSE):
            else_branch = self.parse_stmt()
        return If(cond=cond, then_branch=then_branch, else_branch=else_branch)

    def parse_for(self) -> For:
        self.ts.expect(K.FOR, "Expected 'for'")
        self.ts.expect(K.LPAREN, "Expected '(' after 'for'")

        # init: либо Decl, либо Assign; обязателен, заканчивается ';'
        init = self.parse_for_init()
        self.ts.expect(K.SEMI, "Expected ';' after for-init")

        # cond: опционально выражение до ';'
        cond: Optional[Expr] = None
        if self.ts.peek().kind != K.SEMI:
            cond = self.parse_expr()
        self.ts.expect(K.SEMI, "Expected ';' after for-cond")

        # step: опционально Assign до ')'
        step: Optional[Assign] = None
        if self.ts.peek().kind != K.RPAREN:
            step = self.parse_for_step()
        self.ts.expect(K.RPAREN, "Expected ')' after for-clauses")

        body = self.parse_stmt()
        return For(init=init, cond=cond, step=step, body=body)

    def parse_for_init(self) -> Stmt:
        if self.ts.peek().kind in (K.INT, K.REAL, K.BOOL):
            decl = self.parse_decl_core()
            return decl
        # попробуем присваивание IDENT '=' expr
        name = self.ts.expect(K.IDENT, "Expected identifier in for-init").lexeme
        self.ts.expect(K.ASSIGN, "Expected '=' in for-init")
        expr = self.parse_expr()
        return Assign(name=name, expr=expr)

    def parse_for_step(self) -> Assign:
        name = self.ts.expect(K.IDENT, "Expected identifier in for-step").lexeme
        self.ts.expect(K.ASSIGN, "Expected '=' in for-step")
        expr = self.parse_expr()
        return Assign(name=name, expr=expr)

    def parse_funcdef(self) -> FuncDef:
        is_proc = False
        ret_type: Optional[TypeKind] = None
        if self.ts.match(K.PROC):
            is_proc = True
        else:
            self.ts.expect(K.FUNC, "Expected 'func' or 'proc'")
            # для v1 допустим упрощённую сигнатуру: func <type> name()
            ret_type = self.parse_type()

        name = self.ts.expect(K.IDENT, "Expected function/procedure name").lexeme
        self.ts.expect(K.LPAREN, "Expected '(' after name")
        params: List[str] = []
        # v1: либо пусто, либо список идентификаторов без типов
        if self.ts.peek().kind != K.RPAREN:
            params.append(self.ts.expect(K.IDENT, "Expected parameter name").lexeme)
            while self.ts.match(K.COMMA):
                params.append(self.ts.expect(K.IDENT, "Expected parameter name").lexeme)
        self.ts.expect(K.RPAREN, "Expected ')' after parameters")

        body = self.parse_block()
        return FuncDef(name=name, is_proc=is_proc, ret_type=ret_type, body=body, params=params)

    def parse_return(self) -> Return:
        self.ts.expect(K.RETURN, "Expected 'return'")
        if self.ts.peek().kind == K.SEMI:
            self.ts.advance()  # ';'
            return Return(expr=None)
        expr = self.parse_expr()
        self.ts.expect(K.SEMI, "Expected ';' after return value")
        return Return(expr=expr)

    def parse_read(self) -> ReadStmt:
        self.ts.expect(K.READ, "Expected 'read'")
        self.ts.expect(K.LPAREN, "Expected '(' after 'read'")
        name = self.ts.expect(K.IDENT, "Expected identifier in read(...)").lexeme
        self.ts.expect(K.RPAREN, "Expected ')' after read argument")
        self.ts.expect(K.SEMI, "Expected ';' after read(...)")
        return ReadStmt(name=name)

    def parse_print(self) -> PrintStmt:
        self.ts.expect(K.PRINT, "Expected 'print'")
        self.ts.expect(K.LPAREN, "Expected '(' after 'print'")
        expr = self.parse_expr()
        self.ts.expect(K.RPAREN, "Expected ')' after print argument")
        self.ts.expect(K.SEMI, "Expected ';' after print(...)")
        return PrintStmt(expr=expr)

    def parse_decl_stmt(self) -> Decl:
        decl = self.parse_decl_core()
        self.ts.expect(K.SEMI, "Expected ';' after declaration")
        return decl

    def parse_decl_core(self) -> Decl:
        ty = self.parse_type()
        name = self.ts.expect(K.IDENT, "Expected variable name").lexeme
        init: Optional[Expr] = None
        if self.ts.match(K.ASSIGN):
            init = self.parse_expr()
        return Decl(type=ty, name=name, init=init)

    def parse_type(self) -> TypeKind:
        if self.ts.match(K.INT): return TypeKind.INT
        if self.ts.match(K.REAL): return TypeKind.REAL
        if self.ts.match(K.BOOL): return TypeKind.BOOL
        tok = self.ts.peek()
        raise ParseError(self.ts.last_ok_line, self.ts.last_ok_col, tok, "Expected type (int|real|bool)")

    # === НИЖЕ — КАСКАД ВЫРАЖЕНИЙ Этапа 3. Оставьте как есть в вашем проекте ===
    # Если у вас это в отдельном классе — просто импортируйте. Ниже — минимальная заготовка,
    # замените её на вашу реализацию из Этапа 3.

    def parse_expr(self) -> Expr:
        return self.parse_or()

    def parse_or(self) -> Expr:
        left = self.parse_and()
        while self.ts.match(K.OR):
            right = self.parse_and()
            left = BinOp(op=OpKind.OR, left=left, right=right)
        return left

    def parse_and(self) -> Expr:
        left = self.parse_equality()
        while self.ts.match(K.AND):
            right = self.parse_equality()
            left = BinOp(op=OpKind.AND, left=left, right=right)
        return left

    def parse_equality(self) -> Expr:
        left = self.parse_relational()
        while True:
            if self.ts.match(K.EQ):
                op = OpKind.EQ
            elif self.ts.match(K.NEQ):
                op = OpKind.NEQ
            else:
                break
            right = self.parse_relational()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_relational(self) -> Expr:
        left = self.parse_add()
        while True:
            if self.ts.match(K.LT):
                op = OpKind.LT
            elif self.ts.match(K.LE):
                op = OpKind.LE
            elif self.ts.match(K.GT):
                op = OpKind.GT
            elif self.ts.match(K.GE):
                op = OpKind.GE
            else:
                break
            right = self.parse_add()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_add(self) -> Expr:
        left = self.parse_mul()
        while True:
            if self.ts.match(K.PLUS):
                op = OpKind.ADD
            elif self.ts.match(K.MINUS):
                op = OpKind.SUB
            else:
                break
            right = self.parse_mul()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_mul(self) -> Expr:
        left = self.parse_unary()
        while True:
            if self.ts.match(K.STAR):
                op = OpKind.MUL
            elif self.ts.match(K.SLASH):
                op = OpKind.DIV
            else:
                break
            right = self.parse_unary()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_unary(self) -> Expr:
        if self.ts.match(K.NOT):
            return UnOp(op=OpKind.NOT, expr=self.parse_unary())
        if self.ts.match(K.MINUS):
            return UnOp(op=OpKind.NEG, expr=self.parse_unary())
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        tok = self.ts.peek()
        # литералы
        if self.ts.match(K.INT_LIT):
            return Literal(value=tok.value)
        if self.ts.match(K.REAL_LIT):
            return Literal(value=tok.value)
        if self.ts.match(K.BOOL_LIT):
            # в зависимости от вашего лексера true/false могут быть BOOL с value True/False
            val = tok.value if tok.value is not None else (tok.lexeme == "true")
            return Literal(value=val)
        # идентификатор
        if self.ts.match(K.IDENT):
            return Ident(name=tok.lexeme)
        # (expr)
        if self.ts.match(K.LPAREN):
            e = self.parse_expr()
            self.ts.expect(K.RPAREN, "Expected ')' after expression")
            return e
        raise ParseError(self.ts.last_ok_line, self.ts.last_ok_col, tok, "Expected primary expression")

def parse(tokens: List[Token]) -> Program:
    return Parser(tokens).parse()
