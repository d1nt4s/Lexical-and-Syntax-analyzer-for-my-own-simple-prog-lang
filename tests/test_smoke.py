import builtins
import sys
import tempfile
import os
from importlib import import_module

def test_entry_point_prints_ok(capsys):
    main_mod = import_module("main.main")
    # main() теперь работает через аргументы командной строки и требует путь к файлу
    # Создаем временный файл с пустой программой
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write('')  # Пустая программа
        temp_path = f.name
    
    try:
        # Вызываем main() с путем к файлу и флагом --json
        main_mod.main(['--json', temp_path])
        out = capsys.readouterr().out.strip()
        # Пустая программа должна разобраться в пустой Program
        assert '"type": "Program"' in out
        assert '"stmts": []' in out
    finally:
        # Удаляем временный файл
        if os.path.exists(temp_path):
            os.unlink(temp_path)