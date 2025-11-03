import builtins
from importlib import import_module

def test_entry_point_prints_ok(capsys):
    main_mod = import_module("main.main")
    # перехват stdout
    main_mod.main()
    out = capsys.readouterr().out.strip()
    assert out == "MiniLang pipeline stub: ok"