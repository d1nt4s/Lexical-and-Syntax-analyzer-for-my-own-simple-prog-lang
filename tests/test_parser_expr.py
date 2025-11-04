import json
import pytest
from lexer import Lexer
from parser import parse, ParseError, BinOp, UnOp, Literal, Ident, OpKind

def ast_json(src: str):
    toks = Lexer(src).scan_all()
    prog = parse(toks)
    return prog.to_json()

def test_empty_program_is_allowed():
    j = ast_json("")
    assert j["type"] == "Program"
    assert j["stmts"] == []

def test_simple_literal_and_ident():
    j = ast_json("42; x; true; 2.5;")
    kinds = [stmt["expr"]["type"] for stmt in j["stmts"]]
    assert kinds == ["Literal", "Ident", "Literal", "Literal"]
    assert j["stmts"][0]["expr"]["value"] == 42
    assert j["stmts"][1]["expr"]["name"] == "x"
    assert j["stmts"][2]["expr"]["value"] is True
    assert abs(j["stmts"][3]["expr"]["value"] - 2.5) < 1e-9

def test_parentheses_and_precedence():
    # 1 + 2 * 3 ;  (1 + 2) * 3 ;
    j = ast_json("1 + 2 * 3; (1 + 2) * 3;")
    s1 = j["stmts"][0]["expr"]
    s2 = j["stmts"][1]["expr"]

    # первое: ADD(1, MUL(2,3))
    assert s1["type"] == "BinOp" and s1["op"] == "ADD"
    assert s1["left"]["value"] == 1
    assert s1["right"]["type"] == "BinOp" and s1["right"]["op"] == "MUL"

    # второе: MUL( ADD(1,2), 3 )
    assert s2["type"] == "BinOp" and s2["op"] == "MUL"
    assert s2["left"]["type"] == "BinOp" and s2["left"]["op"] == "ADD"

def test_associativity_left_for_add_and_mul():
    # 8 / 4 / 2 -> (8/4)/2
    j = ast_json("8 / 4 / 2;")
    e = j["stmts"][0]["expr"]
    assert e["op"] == "DIV"
    assert e["left"]["type"] == "BinOp" and e["left"]["op"] == "DIV"
    assert e["right"]["type"] == "Literal" and e["right"]["value"] == 2

def test_unary_binding_tighter_than_mul():
    # -a * b  -> MUL( NEG(a), b )
    j = ast_json("-a * b;")
    e = j["stmts"][0]["expr"]
    assert e["op"] == "MUL"
    assert e["left"]["type"] == "UnOp" and e["left"]["op"] == "NEG"

def test_logic_and_relational_precedence():
    j = ast_json("a || b && c == d < e;")
    e = j["stmts"][0]["expr"]
    # на вершине должен быть OR
    assert e["type"] == "BinOp" and e["op"] == "OR"

def test_missing_semicolon_reports_error():
    with pytest.raises(ParseError) as ei:
        ast_json("1 + 2")
    assert "Expected ';' after expression" in str(ei.value)

def test_unmatched_paren_reports_error():
    with pytest.raises(ParseError) as ei:
        ast_json("(1 + 2;")
    assert "Expected ')' after expression" in str(ei.value)

def test_unexpected_token_in_primary():
    with pytest.raises(ParseError) as ei:
        ast_json("@;")
    assert "Expected primary expression" in str(ei.value)
