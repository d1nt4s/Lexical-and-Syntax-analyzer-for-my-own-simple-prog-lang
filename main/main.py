from __future__ import annotations
import sys, json
from lexer import Lexer, LexError
from parser import parse, ParseError

def main():
    src = sys.stdin.read()
    try:
        toks = Lexer(src).scan_all()
        prog = parse(toks)
        print(json.dumps(prog.to_json(), indent=2))
    except (LexError, ParseError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
