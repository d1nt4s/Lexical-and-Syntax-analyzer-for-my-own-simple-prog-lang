import pytest
from lexer import Lexer, TokenKind, LexError


def kinds(seq):
    return [t.kind for t in seq]


def test_simple_program_tokens():
    src = r"""
        // variable declarations
        int a; real b; bool c;
        a = 10; b = 2.5; c = true;
        /* compute and print */
        if (a >= 10 && c) { print(a + b); }
        else { read(a); }
    """
    toks = Lexer(src).scan_all()

    assert toks[-1].kind == TokenKind.EOF
    assert [t.kind for t in toks[:3]] == [TokenKind.KW_INT, TokenKind.IDENT, TokenKind.SEMI]

    ints = [t for t in toks if t.kind == TokenKind.INT]
    reals = [t for t in toks if t.kind == TokenKind.REAL]
    bools = [t for t in toks if t.kind == TokenKind.BOOL]

    assert any(t.value == 10 for t in ints)
    assert any(abs(t.value - 2.5) < 1e-9 for t in reals)
    assert any(t.value is True for t in bools)

    assert any(t.kind == TokenKind.GE for t in toks)
    assert any(t.kind == TokenKind.AND for t in toks)


def test_block_comment_unterminated():
    src = "int a; /* not closed"
    with pytest.raises(LexError) as ei:
        Lexer(src).scan_all()
    err = ei.value
    assert "Unterminated block comment" in str(err)
    assert err.line == 1


def test_unknown_character():
    src = "print(@);"
    with pytest.raises(LexError) as ei:
        Lexer(src).scan_all()
    msg = str(ei.value)
    assert "Unknown character '@'" in msg


def test_real_requires_digits_on_both_sides():
    src = "x = 1.; y = .5;"
    with pytest.raises(LexError) as ei:
        Lexer(src).scan_all()
    assert "Unexpected '.'" in str(ei.value)
