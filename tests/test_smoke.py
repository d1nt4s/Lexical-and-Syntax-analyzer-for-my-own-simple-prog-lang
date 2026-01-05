import builtins
import sys
import tempfile
import os
from importlib import import_module

def test_entry_point_prints_ok(capsys):
    main_mod = import_module("main.main")
    # main() now works via command line arguments and requires file path
    # Create temporary file with empty program
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write('')  # Empty program
        temp_path = f.name
    
    try:
        # Call main() with file path and --json flag
        main_mod.main(['--json', temp_path])
        out = capsys.readouterr().out.strip()
        # Empty program should parse into empty Program
        assert '"type": "Program"' in out
        assert '"stmts": []' in out
    finally:
        # Remove temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)