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