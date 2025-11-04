import builtins
import sys
from io import StringIO
from importlib import import_module

def test_entry_point_prints_ok(capsys):
    main_mod = import_module("main.main")
    # Мокируем stdin - передаем пустую строку, чтобы парсер разобрал пустую программу
    old_stdin = sys.stdin
    sys.stdin = StringIO("")
    try:
        main_mod.main()
        out = capsys.readouterr().out.strip()
        # Пустая программа должна разобраться в пустой Program
        assert '"type": "Program"' in out
        assert '"stmts": []' in out
    finally:
        sys.stdin = old_stdin