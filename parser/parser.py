from __future__ import annotations
from typing import List, Optional
from lexer.tokens import Token, TokenKind
from parser.ast import (
    Program, Stmt, Block, Decl, Assign, If, For, FuncDef, CallStmt,
    PrintStmt, ReadStmt, Return, ExprStmt,
    Expr, BinOp, UnOp, Literal, Ident, IndexExpr, CallExpr, FieldAccessExpr, OpKind, TypeKind,
    TypeSpec, BaseType, ArrayType, NamedStructType, Param,
    EnumDecl, StructDecl, FieldDecl
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
    LBRACKET = TokenKind.LBRACKET
    RBRACKET = TokenKind.RBRACKET
    DOT = TokenKind.DOT
    COMMA = TokenKind.COMMA
    SEMI = TokenKind.SEMI
    EOF = TokenKind.EOF
    ENUM = TokenKind.KW_ENUM
    STRUCT = TokenKind.KW_STRUCT
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
        # enum
        if tok.kind == K.ENUM:
            return self.parse_enum_decl()
        # struct
        if tok.kind == K.STRUCT:
            # Проверяем, что это объявление struct, а не тип struct Name
            # Если следующий токен IDENT, а затем LBRACE - это объявление
            if self.ts.i + 1 < len(self.ts.toks) and self.ts.toks[self.ts.i + 1].kind == K.IDENT:
                if self.ts.i + 2 < len(self.ts.toks) and self.ts.toks[self.ts.i + 2].kind == K.LBRACE:
                    return self.parse_struct_decl()
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
        # объявления типов (int, real, bool, struct Name)
        if tok.kind in (K.INT, K.REAL, K.BOOL) or (tok.kind == K.STRUCT):
            return self.parse_decl_stmt()
        # присваивание или вызов/expr;
        # Присваивание может начинаться только с IDENT или LPAREN (для индексирования)
        # Для остальных сразу парсим как выражение
        if tok.kind == K.IDENT or tok.kind == K.LPAREN:
            # Попытка присваивания: lvalue (Ident или IndexExpr) '=' expr ';'
            # Сохраняем позицию для отката, если это не присваивание
            save_i = self.ts.i
            lvalue = self.parse_postfix()  # может быть Ident или IndexExpr
            if self.ts.match(K.ASSIGN):
                expr = self.parse_expr()
                self.ts.expect(K.SEMI, "Expected ';' after assignment")
                if not isinstance(lvalue, (Ident, IndexExpr, FieldAccessExpr)):
                    raise ParseError(self.ts.last_ok_line, self.ts.last_ok_col, 
                                   self.ts.peek(), "Assignment target must be identifier, indexed expression, or field access")
                return Assign(lvalue=lvalue, expr=expr)
            # Не присваивание - откатываемся и парсим как выражение
            self.ts.i = save_i
            expr = self.parse_expr()
            self.ts.expect(K.SEMI, "Expected ';' after expression")
            return ExprStmt(expr=expr)
        # Обычные выражения (литералы, унарные операторы и т.д.)
        if tok.kind in (K.MINUS, K.NOT, K.PLUS, K.INT_LIT, K.REAL_LIT, K.BOOL_LIT):
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
        # попробуем присваивание lvalue '=' expr
        lvalue = self.parse_postfix()
        self.ts.expect(K.ASSIGN, "Expected '=' in for-init")
        expr = self.parse_expr()
        if not isinstance(lvalue, (Ident, IndexExpr, FieldAccessExpr)):
            raise ParseError(self.ts.last_ok_line, self.ts.last_ok_col, 
                           self.ts.peek(), "Assignment target must be identifier, indexed expression, or field access")
        return Assign(lvalue=lvalue, expr=expr)

    def parse_for_step(self) -> Assign:
        lvalue = self.parse_postfix()
        self.ts.expect(K.ASSIGN, "Expected '=' in for-step")
        expr = self.parse_expr()
        if not isinstance(lvalue, (Ident, IndexExpr, FieldAccessExpr)):
            raise ParseError(self.ts.last_ok_line, self.ts.last_ok_col, 
                           self.ts.peek(), "Assignment target must be identifier, indexed expression, or field access")
        return Assign(lvalue=lvalue, expr=expr)

    def parse_param(self) -> Param:
        """Parse a typed parameter: type IDENT"""
        type_spec = self.parse_type()
        name = self.ts.expect(K.IDENT, "Expected parameter name").lexeme
        return Param(type_spec=type_spec, name=name)

    def parse_param_list(self) -> List[Param]:
        """Parse parameter list: (param (',' param)*)?"""
        params: List[Param] = []
        if self.ts.peek().kind == K.RPAREN:
            return params
        while True:
            params.append(self.parse_param())
            if self.ts.match(K.COMMA):
                continue
            break
        return params

    def parse_funcdef(self) -> FuncDef:
        is_proc = False
        ret_type: Optional[TypeSpec] = None
        if self.ts.match(K.PROC):
            is_proc = True
        else:
            self.ts.expect(K.FUNC, "Expected 'func' or 'proc'")
            # func требует тип возвращаемого значения
            ret_type = self.parse_type()

        name = self.ts.expect(K.IDENT, "Expected function/procedure name").lexeme
        self.ts.expect(K.LPAREN, "Expected '(' after name")
        params = self.parse_param_list()
        self.ts.expect(K.RPAREN, "Expected ')' after parameters")

        body = self.parse_block()
        return FuncDef(name=name, is_proc=is_proc, ret_type=ret_type, body=body, params=params)

    def parse_enum_decl(self) -> EnumDecl:
        """Parse enum declaration: enum Name { A, B, C }"""
        self.ts.expect(K.ENUM, "Expected 'enum'")
        name = self.ts.expect(K.IDENT, "Expected enum name").lexeme
        self.ts.expect(K.LBRACE, "Expected '{' after enum name")
        members: List[str] = []
        if self.ts.peek().kind != K.RBRACE:
            while True:
                member_tok = self.ts.expect(K.IDENT, "Expected enum member name")
                members.append(member_tok.lexeme)
                if self.ts.match(K.COMMA):
                    # Проверяем, не является ли следующая лексема закрывающей скобкой
                    if self.ts.peek().kind == K.RBRACE:
                        raise ParseError(self.ts.last_ok_line, self.ts.last_ok_col,
                                       self.ts.peek(), "Expected enum member name")
                    continue
                break
        self.ts.expect(K.RBRACE, "Expected '}' after enum members")
        return EnumDecl(name=name, members=members)

    def parse_struct_decl(self) -> StructDecl:
        """Parse struct declaration: struct Name { type field; ... }"""
        self.ts.expect(K.STRUCT, "Expected 'struct'")
        name = self.ts.expect(K.IDENT, "Expected struct name").lexeme
        self.ts.expect(K.LBRACE, "Expected '{' after struct name")
        fields: List[FieldDecl] = []
        while self.ts.peek().kind != K.RBRACE:
            if self.ts.match(K.SEMI):  # пропустим пустые строки
                continue
            field_type = self.parse_type()
            field_name = self.ts.expect(K.IDENT, "Expected field name").lexeme
            self.ts.expect(K.SEMI, "Expected ';' after field declaration")
            fields.append(FieldDecl(type_spec=field_type, name=field_name))
        self.ts.expect(K.RBRACE, "Expected '}' after struct body")
        return StructDecl(name=name, fields=fields)

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
        type_spec = self.parse_type()
        name = self.ts.expect(K.IDENT, "Expected variable name").lexeme
        init: Optional[Expr] = None
        if self.ts.match(K.ASSIGN):
            init = self.parse_expr()
        return Decl(type_spec=type_spec, name=name, init=init)

    def parse_type(self) -> TypeSpec:
        # Parse base type or struct name
        base: TypeSpec
        if self.ts.match(K.INT):
            base = BaseType(kind=TypeKind.INT)
        elif self.ts.match(K.REAL):
            base = BaseType(kind=TypeKind.REAL)
        elif self.ts.match(K.BOOL):
            base = BaseType(kind=TypeKind.BOOL)
        elif self.ts.match(K.STRUCT):
            # struct Name
            name = self.ts.expect(K.IDENT, "Expected struct name after 'struct'").lexeme
            base = NamedStructType(name=name)
        else:
            tok = self.ts.peek()
            raise ParseError(self.ts.last_ok_line, self.ts.last_ok_col, tok, "Expected type (int|real|bool|struct Name)")
        
        # Parse array dimensions: []*
        dims = 0
        while self.ts.peek().kind == K.LBRACKET:
            self.ts.expect(K.LBRACKET, "Expected '['")
            self.ts.expect(K.RBRACKET, "Expected ']' after '['")
            dims += 1
        
        if dims > 0:
            return ArrayType(base=base, dims=dims)
        return base

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
        return self.parse_postfix()

    def parse_arguments(self) -> List[Expr]:
        """Parse argument list: (expr (',' expr)*)?"""
        args: List[Expr] = []
        if self.ts.peek().kind == K.RPAREN:
            return args
        while True:
            args.append(self.parse_expr())
            if self.ts.match(K.COMMA):
                continue
            break
        return args

    def parse_postfix(self) -> Expr:
        """Parse postfix expressions: primary ('(' args? ')' | '[' expr ']' | '.' IDENT)*"""
        expr = self.parse_primary()
        # Parse function calls, array indexing, and field access: ('(' args? ')' | '[' expr ']' | '.' IDENT)*
        while True:
            # Function call: IDENT '(' args? ')'
            if isinstance(expr, Ident) and self.ts.match(K.LPAREN):
                args = self.parse_arguments()
                self.ts.expect(K.RPAREN, "Expected ')' after arguments")
                expr = CallExpr(callee=expr.name, args=args)
                continue
            # Array indexing: [expr]
            elif self.ts.match(K.LBRACKET):
                if self.ts.peek().kind == K.RBRACKET:
                    # Empty index - error
                    raise ParseError(self.ts.last_ok_line, self.ts.last_ok_col, 
                                   self.ts.peek(), "Expected expression inside []")
                index_expr = self.parse_expr()
                self.ts.expect(K.RBRACKET, "Expected ']' after index expression")
                expr = IndexExpr(base=expr, index=index_expr)
                continue
            # Field access: .IDENT
            elif self.ts.match(K.DOT):
                field_name = self.ts.expect(K.IDENT, "Expected field name after '.'").lexeme
                expr = FieldAccessExpr(base=expr, field=field_name)
                continue
            else:
                break
        return expr

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
