import subprocess, pathlib

for f in sorted(pathlib.Path("examples").glob("*.txt")):
    print(f"=== {f} ===")
    result = subprocess.run(
        ["python", "-m", "main.main", str(f)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(result.stdout.strip())
    else:
        print(result.stderr.strip())
        print("(ошибка как ожидается)")
    print()
