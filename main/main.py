"""
CLI: parse a source file and print AST (pretty or JSON) or generate IR.

Usage:
  python -m main.main <path/to/source.txt> [--json] [--ir] [--ir-output <file>]
Exit codes:
  0 on success, 1 on lex/parse/semantic error.
"""
import sys
import json

from lexer import scan_all
from parser import parse
from parser.errors import ParseError
from semantic.analyzer import analyze
from semantic.errors import SemanticError
from intermidiate.generator import generate_ir
from intermidiate.ir import ir_to_string

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__.strip())
        return 0

    path = None
    as_json = False
    generate_ir_code = False
    ir_output_file = None
    
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--json":
            as_json = True
        elif a == "--ir":
            generate_ir_code = True
        elif a == "--ir-output":
            if i + 1 < len(argv):
                ir_output_file = argv[i + 1]
                i += 1
            else:
                print("ERROR: --ir-output requires a filename", file=sys.stderr)
                return 1
        elif a.startswith("-"):
            print(f"Unknown option: {a}", file=sys.stderr)
            print(__doc__.strip(), file=sys.stderr)
            return 1
        else:
            path = a
        i += 1

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
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    try:
        analyze(program)
    except SemanticError as e:
        print(e.format_error(), file=sys.stderr)
        return 1

    if generate_ir_code:
        try:
            ir_program = generate_ir(program)
            ir_code = ir_to_string(ir_program)
            
            if ir_output_file:
                try:
                    with open(ir_output_file, "w", encoding="utf-8") as f:
                        f.write(ir_code)
                    print(f"IR code written to {ir_output_file}", file=sys.stderr)
                except OSError as e:
                    print(f"ERROR: cannot write IR to '{ir_output_file}': {e}", file=sys.stderr)
                    return 1
            else:
                print(ir_code)
        except Exception as e:
            print(f"ERROR: IR generation failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1
        return 0

    if as_json:
        print(json.dumps(program.to_json(), ensure_ascii=False, indent=2))
    else:
        print(program.pretty().rstrip())

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
