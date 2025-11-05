"""
CLI: parse a source file and print AST (pretty or JSON).

Usage:
  python -m main.main <path/to/source.txt> [--json]
Exit codes:
  0 on success, 1 on lex/parse error.
"""
import sys
import json

from lexer import scan_all  # твоя функция лексера: scan_all(src) -> list[Token]
from parser import parse    # твоя функция парсера: parse(tokens) -> Program
from parser.errors import ParseError

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__.strip())
        return 0

    path = None
    as_json = False
    for a in argv:
        if a == "--json":
            as_json = True
        elif a.startswith("-"):
            print(f"Unknown option: {a}", file=sys.stderr)
            print(__doc__.strip(), file=sys.stderr)
            return 1
        else:
            path = a

    if not path:
        print("ERROR: Missing input file.\n", file=sys.stderr)
        print(__doc__.strip(), file=sys.stderr)
        return 1

    try:
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
    except OSError as e:
        print(f"ERROR: cannot read file '{path}': {e}", file=sys.stderr)
        return 1

    # Lexer -> Parser
    try:
        tokens = scan_all(src)
        program = parse(tokens)
    except ParseError as e:
        print(f"PARSE ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        # сюда попадут лексические ошибки, если ты их бросаешь как Exception
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Output
    if as_json:
        print(json.dumps(program.to_json(), ensure_ascii=False, indent=2))
    else:
        print(program.pretty().rstrip())

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
