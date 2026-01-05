"""
Tests for semantic analysis.
"""
from lexer import scan_all
from parser import parse
from semantic.analyzer import analyze
from semantic.errors import SemanticError


def parse_and_analyze(src: str):
    """Parse source code and run semantic analysis."""
    tokens = scan_all(src)
    program = parse(tokens)
    analyze(program)
    return program


def test_missing_main_function():
    """Test that missing main function raises semantic error."""
    src = """
    int x = 10;
    """
    try:
        parse_and_analyze(src)
        assert False, "Should have raised SemanticError"
    except SemanticError as e:
        error_msg = str(e)
        assert "main" in error_msg.lower() or "TYPE_ERROR" in error_msg, f"Error message should mention 'main', got: {error_msg}"


def test_multiple_main_functions():
    """Test that multiple main functions raise semantic error."""
    src = """
    proc main() {
        print(1);
    }
    proc main() {
        print(2);
    }
    """
    try:
        parse_and_analyze(src)
        assert False, "Should have raised SemanticError"
    except SemanticError as e:
        error_msg = str(e)
        assert "main" in error_msg.lower() or "TYPE_ERROR" in error_msg, f"Error message should mention 'main', got: {error_msg}"


def test_type_mismatch_int_plus_real():
    """Test that type mismatch (int + real) is caught."""
    src = """
    proc main() {
        int x = 10;
        real y = 3.14;
        int z = x + y;  // Should fail: int + real
    }
    """
    try:
        parse_and_analyze(src)
        assert False, "Should have raised SemanticError"
    except SemanticError as e:
        error_msg = str(e)
        assert "TYPE_ERROR" in error_msg, f"Error should contain 'TYPE_ERROR', got: {error_msg}"
        assert ("type mismatch" in error_msg.lower() or 
                "arithmetic operands" in error_msg.lower() or
                "same type" in error_msg.lower()), f"Error should mention type mismatch, got: {error_msg}"
        
        # Check that error has span information
        assert e.node is not None, "Error should have node"
        assert e.node.span is not None, "Error node should have span"


def test_type_mismatch_bool_plus_int():
    """Test that type mismatch (bool + int) is caught."""
    src = """
    proc main() {
        bool x = true;
        int y = 10;
        int z = x + y;  // Should fail: bool + int
    }
    """
    try:
        parse_and_analyze(src)
        assert False, "Should have raised SemanticError"
    except SemanticError as e:
        error_msg = str(e)
        assert "TYPE_ERROR" in error_msg, f"Error should contain 'TYPE_ERROR', got: {error_msg}"


def test_invalid_cast_real_to_int_with_fractional():
    """Test that invalid cast (real to int with non-zero fractional part) is caught."""
    src = """
    proc main() {
        real x = 1.2;
        int y = int(x);  // Should fail: cannot cast real to int
    }
    """
    try:
        parse_and_analyze(src)
        assert False, "Should have raised SemanticError"
    except SemanticError as e:
        error_msg = str(e)
        assert "TYPE_ERROR" in error_msg, f"Error should contain 'TYPE_ERROR', got: {error_msg}"
        assert ("cast" in error_msg.lower() or "kastovanje" in error_msg.lower() or "Invalid cast" in error_msg), \
            f"Error should mention cast, got: {error_msg}"
        
        # Check that error has span information
        assert e.node is not None, "Error should have node"
        assert e.node.span is not None, "Error node should have span"


def test_invalid_cast_literal_real_to_int_with_fractional():
    """Test that invalid cast (literal real to int with non-zero fractional part) is caught."""
    src = """
    proc main() {
        int y = int(1.2);  // Should fail: literal real with non-zero fractional part
    }
    """
    try:
        parse_and_analyze(src)
        assert False, "Should have raised SemanticError"
    except SemanticError as e:
        error_msg = str(e)
        assert "TYPE_ERROR" in error_msg, f"Error should contain 'TYPE_ERROR', got: {error_msg}"
        assert ("cast" in error_msg.lower() or "kastovanje" in error_msg.lower() or "Invalid cast" in error_msg), \
            f"Error should mention cast, got: {error_msg}"


def test_valid_cast_real_to_int_zero_fractional():
    """Test that valid cast (real to int with zero fractional part) works."""
    src = """
    proc main() {
        int x = int(3.0);  // Should work: literal real with zero fractional part
        int y = int(5.0);  // Should work
    }
    """
    # Should not raise any error
    program = parse_and_analyze(src)
    assert program is not None


def test_valid_cast_int_to_real():
    """Test that valid cast (int to real) works."""
    src = """
    proc main() {
        int x = 10;
        real y = real(x);  // Should work: int to real is always allowed
    }
    """
    # Should not raise any error
    program = parse_and_analyze(src)
    assert program is not None


def test_indexing_non_array():
    """Test that indexing non-array is caught."""
    src = """
    proc main() {
        int x = 10;
        int y = x[0];  // Should fail: x is not an array
    }
    """
    try:
        parse_and_analyze(src)
        assert False, "Should have raised SemanticError"
    except SemanticError as e:
        error_msg = str(e)
        assert "TYPE_ERROR" in error_msg, f"Error should contain 'TYPE_ERROR', got: {error_msg}"
        assert ("array" in error_msg.lower() or "index" in error_msg.lower()), \
            f"Error should mention array/index, got: {error_msg}"
        
        # Check that error has span information
        assert e.node is not None, "Error should have node"
        assert e.node.span is not None, "Error node should have span"


def test_indexing_array_with_non_int():
    """Test that indexing array with non-int index is caught."""
    src = """
    proc main() {
        int[] a;
        real x = 3.14;
        int y = a[x];  // Should fail: index must be int
    }
    """
    try:
        parse_and_analyze(src)
        assert False, "Should have raised SemanticError"
    except SemanticError as e:
        error_msg = str(e)
        assert "TYPE_ERROR" in error_msg, f"Error should contain 'TYPE_ERROR', got: {error_msg}"
        assert ("index" in error_msg.lower() or "int" in error_msg.lower()), \
            f"Error should mention index/int, got: {error_msg}"


def test_valid_main_function():
    """Test that valid main function passes semantic analysis."""
    src = """
    proc main() {
        int x = 10;
        print(x);
    }
    """
    # Should not raise any error
    program = parse_and_analyze(src)
    assert program is not None
    assert len(program.stmts) > 0


def test_semantic_error_has_span():
    """Test that semantic errors include span information with line:col."""
    src = """
    proc main() {
        int x = 10;
        real y = 3.14;
        int z = x + y;
    }
    """
    try:
        parse_and_analyze(src)
        assert False, "Should have raised SemanticError"
    except SemanticError as e:
        # Check that error can be formatted with position
        formatted = e.format_error()
        assert ":" in formatted, f"Formatted error should contain ':', got: {formatted}"
        # Should have line number (at least line 5 where the error is)
        assert any(char.isdigit() for char in formatted), f"Formatted error should contain digits, got: {formatted}"

