# Compiler Project

A compiler for a mini-language with lexer, parser, semantic analyzer, and IR code generation.

## Project Structure

```
Project1/
├── lexer/          # Lexical analysis
├── parser/         # Syntax analysis (AST)
├── semantic/       # Semantic analysis
├── intermidiate/   # IR code generation
├── main/           # Main entry point
├── examples/        # Test examples
└── tests/          # Unit tests
```

## Quick Start

### Basic Usage

Parse a source file and print AST:
```bash
python3 -m main.main examples/ok_01_basic.txt
```

Generate IR code:
```bash
python3 -m main.main examples/ok_01_basic.txt --ir
```

Save IR to file:
```bash
python3 -m main.main examples/ok_01_basic.txt --ir --ir-output output.ir
```

### Examples

**Valid examples** (`ok_*.txt`):
- `ok_01_basic.txt` - declarations, assignments, print
- `ok_02_if.txt` - if/else statements
- `ok_03_for.txt` - for loops
- `ok_04_func.txt` - functions with return
- `ok_05_proc.txt` - procedures
- `ok_06_array.txt` - arrays (load/store)
- `ok_07_struct.txt` - structs (field access)
- `ok_08_cast.txt` - valid type casting (real to int with zero fractional part)

**Error examples** (`err_*.txt`):
- `err_lex_01.txt` - lexical error (unknown character)
- `err_syn_01.txt` - syntax error (missing semicolon)
- `err_sem_01.txt` - semantic error (undeclared variable)
- `err_sem_02.txt` - semantic error (unknown struct field)
- `err_sem_03.txt` - semantic error (type mismatch: int + real without casting)
- `err_sem_04.txt` - semantic error (invalid cast: real to int with non-zero fractional part)

### Testing

Run all valid examples:
```bash
for f in examples/ok_*.txt; do
  echo "=== $f ==="
  python3 -m main.main "$f" --ir
  echo
done
```

Test error handling:
```bash
for f in examples/err_*.txt; do
  echo "=== $f ==="
  python3 -m main.main "$f" 2>&1
  echo
done
```

## IR Instructions

Stack machine operations:
- `push <value>` - push value onto stack
- `load <name>` - load variable value
- `store <name>` - store value to variable
- `add`, `sub`, `mul`, `div` - arithmetic operations
- `lt`, `le`, `gt`, `ge`, `eq`, `neq` - comparisons
- `and`, `or`, `not` - logical operations
- `load_index` - load array element
- `store_index` - store to array element
- `load_field <field>` - load struct field
- `store_field <field>` - store to struct field
- `call <name>` - call function
- `ret` - return from procedure
- `retv` - return from function with value
- `label <name>` - label for jumps
- `jmp <label>` - unconditional jump
- `jmp_if_false <label>` - conditional jump
- `pop` - remove top value from stack

## Stack Contract

- `gen_expr(expr)` always leaves exactly 1 value on stack
- `gen_stmt(stmt)` leaves stack empty (no garbage)
- `jmp_if_false` consumes bool from stack

## Error Messages

- **Lexical errors**: `ERROR: LexError at line:col: message`
- **Syntax errors**: `PARSE ERROR: ParseError near line:col: message`
- **Semantic errors**: `Semantic error: line:col: message`

## Requirements

- Python 3.8+

## Documentation

See `intermidiate/README.md` for detailed IR documentation and `intermidiate/EXPLANATION.md` for IR generation explanation.
