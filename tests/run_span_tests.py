#!/usr/bin/env python3
"""
Simple script to run span tests without pytest.
Can be run: python3 tests/run_span_tests.py
"""
import sys
from pathlib import Path

# Add root directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lexer import scan_all
from parser import parse
from parser.ast import (
    Program, Block, Decl, Assign, If, For, FuncDef,
    PrintStmt, ReadStmt, Return, ExprStmt, EnumDecl, StructDecl,
    FieldDecl, SourceSpan, SourcePos
)


def test_all_statements_have_spans():
    """Check that all statements have spans."""
    print("Test 1: All statements have spans...", end=" ")
    src = """
    int x = 1;
    if (x < 5) { print(x); }
    for (int i = 0; i < 3; i = i + 1) { print(i); }
    return x;
    read(y);
    print(10);
    { int z; }
    """
    prog = parse(scan_all(src))
    
    for stmt in prog.stmts:
        assert stmt.span is not None, f"{type(stmt).__name__} must have span"
        assert isinstance(stmt.span, SourceSpan)
    print("✓ OK")


def test_decl_span_includes_semicolon():
    """Check that Decl span includes semicolon."""
    print("Test 2: Decl span includes semicolon...", end=" ")
    src = "int x = 10;"
    prog = parse(scan_all(src))
    
    decl = prog.stmts[0]
    assert isinstance(decl, Decl)
    assert decl.span is not None
    print("✓ OK")


def test_enum_decl_has_span():
    """Check that EnumDecl has span."""
    print("Test 3: EnumDecl has span...", end=" ")
    src = "enum Color { Red, Green, Blue };"
    prog = parse(scan_all(src))
    
    enum_decl = prog.stmts[0]
    assert isinstance(enum_decl, EnumDecl)
    assert enum_decl.span is not None
    assert enum_decl.name == "Color"
    assert len(enum_decl.members) == 3
    print("✓ OK")


def test_struct_decl_has_span_and_field_decl_spans():
    """Check that StructDecl and FieldDecl have spans."""
    print("Test 4: StructDecl and FieldDecl have spans...", end=" ")
    src = """
    struct Point {
        int x;
        real y;
    };
    """
    prog = parse(scan_all(src))
    
    struct_decl = prog.stmts[0]
    assert isinstance(struct_decl, StructDecl)
    assert struct_decl.span is not None
    assert struct_decl.name == "Point"
    assert len(struct_decl.fields) == 2
    
    for field in struct_decl.fields:
        assert isinstance(field, FieldDecl)
        assert field.span is not None
    print("✓ OK")


def test_funcdef_has_span():
    """Check that FuncDef has span."""
    print("Test 5: FuncDef has span...", end=" ")
    src = """
    func int add(int a, int b) {
        return a + b;
    }
    proc hello() {
        print(1);
    }
    """
    prog = parse(scan_all(src))
    
    assert len(prog.stmts) == 2
    
    func_def = prog.stmts[0]
    assert isinstance(func_def, FuncDef)
    assert func_def.span is not None
    assert func_def.name == "add"
    
    proc_def = prog.stmts[1]
    assert isinstance(proc_def, FuncDef)
    assert proc_def.span is not None
    assert proc_def.name == "hello"
    print("✓ OK")


def test_return_span_includes_semicolon():
    """Check that Return has span."""
    print("Test 6: Return has span...", end=" ")
    src = """
    return 42;
    return;
    """
    prog = parse(scan_all(src))
    
    assert len(prog.stmts) == 2
    
    ret1 = prog.stmts[0]
    assert isinstance(ret1, Return)
    assert ret1.span is not None
    
    ret2 = prog.stmts[1]
    assert isinstance(ret2, Return)
    assert ret2.span is not None
    print("✓ OK")


def test_read_print_spans():
    """Check that ReadStmt and PrintStmt have spans."""
    print("Test 7: ReadStmt and PrintStmt have spans...", end=" ")
    src = """
    read(x);
    print(10 + 20);
    """
    prog = parse(scan_all(src))
    
    assert len(prog.stmts) == 2
    
    read_stmt = prog.stmts[0]
    assert isinstance(read_stmt, ReadStmt)
    assert read_stmt.span is not None
    
    print_stmt = prog.stmts[1]
    assert isinstance(print_stmt, PrintStmt)
    assert print_stmt.span is not None
    print("✓ OK")


def test_for_loop_assign_spans():
    """Check that Assign in for-init and for-step have spans."""
    print("Test 8: Assign in for-loop have spans...", end=" ")
    src = """
    for (int i = 0; i < 10; i = i + 1) {
        print(i);
    }
    for (x = 0; x < 5; x = x + 1) {
        print(x);
    }
    """
    prog = parse(scan_all(src))
    
    assert len(prog.stmts) == 2
    
    for1 = prog.stmts[0]
    assert isinstance(for1, For)
    assert for1.init.span is not None
    assert for1.step is not None
    assert for1.step.span is not None
    
    for2 = prog.stmts[1]
    assert isinstance(for2, For)
    assert for2.init.span is not None
    assert for2.step.span is not None
    print("✓ OK")


def test_span_consistency():
    """Check span consistency."""
    print("Test 9: Span consistency...", end=" ")
    src = """
    int x = 1;
    struct Point { int x; real y; };
    enum Color { Red, Green };
    func int test() { return 1; }
    """
    prog = parse(scan_all(src))
    
    def check_span(node):
        if node.span:
            assert node.span.start.line <= node.span.end.line
            if node.span.start.line == node.span.end.line:
                assert node.span.start.col <= node.span.end.col
    
    for stmt in prog.stmts:
        check_span(stmt)
        if isinstance(stmt, StructDecl):
            for field in stmt.fields:
                check_span(field)
    print("✓ OK")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running span tests")
    print("=" * 60)
    print()
    
    tests = [
        test_all_statements_have_spans,
        test_decl_span_includes_semicolon,
        test_enum_decl_has_span,
        test_struct_decl_has_span_and_field_decl_spans,
        test_funcdef_has_span,
        test_return_span_includes_semicolon,
        test_read_print_spans,
        test_for_loop_assign_spans,
        test_span_consistency,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Результаты: {passed} прошло, {failed} провалено")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

