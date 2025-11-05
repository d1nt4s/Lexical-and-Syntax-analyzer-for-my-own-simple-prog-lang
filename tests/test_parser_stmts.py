import pytest

# Допустим в проекте уже есть:
# - lexer.scan_all(src) -> list[Token]
# - parser.parse(tokens) -> Program
# - parser.ast.* классы
from lexer import scan_all
from parser import parse
from parser.ast import (
    Program, Block, Decl, Assign, If, For,
    PrintStmt, ReadStmt, Return, ExprStmt,
    BinOp, UnOp, Literal, Ident, OpKind, TypeKind
)
from parser.errors import ParseError


def parse_src(src: str) -> Program:
    tokens = scan_all(src)
    return parse(tokens)


def test_decl_and_assign_block():
    src = """
    {
      int a;
      real b = 2.5;
      bool c = true;
      a = 10;
    }
    """
    prog = parse_src(src)
    assert isinstance(prog, Program)
    assert len(prog.stmts) == 1
    blk = prog.stmts[0]
    assert isinstance(blk, Block)
    # block contains: Decl, Decl, Decl, Assign
    assert [type(s).__name__ for s in blk.stmts] == ["Decl", "Decl", "Decl", "Assign"]

    d0, d1, d2, asg = blk.stmts
    assert d0.type is TypeKind.INT and d0.name == "a" and d0.init is None
    assert d1.type is TypeKind.REAL and d1.name == "b" and isinstance(d1.init, Literal)
    assert d2.type is TypeKind.BOOL and d2.name == "c" and isinstance(d2.init, Literal)
    assert asg.name == "a" and isinstance(asg.expr, Literal)


def test_if_else_with_block_and_io():
    src = """
    int x = 1;
    if (x < 5) { print(x); }
    else { read(x); }
    """
    prog = parse_src(src)
    assert len(prog.stmts) == 2
    decl, iff = prog.stmts
    assert isinstance(decl, Decl)
    assert isinstance(iff, If)
    # cond is (x < 5)
    assert isinstance(iff.cond, BinOp) and iff.cond.op is OpKind.LT
    # then { print(x); }
    assert isinstance(iff.then_branch, Block)
    then_stmts = iff.then_branch.stmts
    assert len(then_stmts) == 1 and isinstance(then_stmts[0], PrintStmt)
    # else { read(x); }
    assert iff.else_branch is not None
    else_stmts = iff.else_branch.stmts
    assert len(else_stmts) == 1 and isinstance(else_stmts[0], ReadStmt)


def test_for_loop_minimal():
    src = """
    for (int i = 0; i < 3; i = i + 1) {
      print(i);
    }
    """
    prog = parse_src(src)
    assert len(prog.stmts) == 1
    loop = prog.stmts[0]
    assert isinstance(loop, For)
    # init decl
    assert isinstance(loop.init, Decl) and loop.init.name == "i"
    # cond i < 3
    assert isinstance(loop.cond, BinOp) and loop.cond.op is OpKind.LT
    # step i = i + 1
    assert loop.step is not None and isinstance(loop.step, Assign)
    assert isinstance(loop.step.expr, BinOp) and loop.step.expr.op is OpKind.ADD
    # body
    assert isinstance(loop.body, Block)
    assert len(loop.body.stmts) == 1 and isinstance(loop.body.stmts[0], PrintStmt)


def test_expression_stmt_and_unary():
    src = """
    int x; x = -10; print(!false);
    """
    prog = parse_src(src)
    assert len(prog.stmts) == 3
    assert isinstance(prog.stmts[0], Decl)
    assert isinstance(prog.stmts[1], Assign)
    pr = prog.stmts[2]
    assert isinstance(pr, PrintStmt)
    # print argument is UnOp(NOT, Literal)
    assert isinstance(pr.expr, UnOp) and pr.expr.op is OpKind.NOT


def test_return_with_value_and_empty():
    src = """
    { return 1; return; }
    """
    prog = parse_src(src)
    blk = prog.stmts[0]
    assert isinstance(blk, Block)
    assert [type(s).__name__ for s in blk.stmts] == ["Return", "Return"]


# --- Негативные тесты (синтаксические ошибки) ---

def test_error_missing_semicolon_after_decl():
    src = "int x\nx = 1;"
    with pytest.raises(ParseError):
        parse_src(src)


def test_error_missing_rparen_in_if():
    src = "int x = 1; if (x < 3 { print(x); }"
    with pytest.raises(ParseError):
        parse_src(src)


def test_error_missing_rbrace_in_block():
    src = "{ int a; print(a);"
    with pytest.raises(ParseError):
        parse_src(src)


# --- (Необязательно) включи тесты на proc/func, если лексер их поддерживает ---
# Раскомментируй, когда будут токены KW_PROC/KW_FUNC и базовая поддержка сигнатур.
#
# def test_proc_and_func_roundtrip():
#     src = '''
#     proc hello() { print(1); }
#     func int twice(x) { return x + x; }
#     '''
#     prog = parse_src(src)
#     assert len(prog.stmts) == 2
