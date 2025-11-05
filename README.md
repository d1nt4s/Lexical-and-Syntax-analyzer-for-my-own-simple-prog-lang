# Programming Languages — Homework 1 (Stage 5)

**Goal:** deliver a ready-to-submit package with examples, a CLI entry point, and packaging instructions.

## Quick Start

```bash
# Run tests (assumes pytest already set up)
pytest -q

# Pretty-print AST:
python -m main.main examples/valid01_basics.txt

# JSON AST:
python -m main.main examples/valid01_basics.txt --json

# Running all examples
python scripts/run_all_examples.py

# Run a single example (JSON AST)
python -m main.main examples/valid_arrays_1.txt --json

# Run all examples (POSIX shell)
for f in examples/*.txt; do
  echo ">>> $f"
  python -m main.main "$f" --json || true
done

## Enums and Structs

### Enum declarations
```minilang
enum Color { Red, Green, Blue }
enum Direction { North, South, East, West }
```

### Struct declarations
```minilang
struct Point {
  int x;
  int y;
}
```

### Nominal struct type in declarations
```minilang
struct Point p;
struct Point[] points;
```

### Field access
```minilang
p.x = 10;
p.y = 20;
print(p.x);
```

### Chaining with calls/indices
```minilang
arr[i].x = 1;
print(arr[i].x);
get().p[i].x;
```

### Run enum/struct examples
```bash
python -m main.main examples/valid_enum_struct_1.txt --json
python -m main.main examples/valid_struct_array_field_chain.txt --json
python -m main.main examples/valid_call_field_index_mix.txt --json
```

## Calls and typed parameters

# Function with typed parameters
func int add(int a, int b) { return a + b; }

# Procedure with typed parameter
proc show(int x) { print(x); }

# Run samples
python -m main.main examples/valid_calls_1.txt --json
python -m main.main examples/valid_calls_2.txt --json