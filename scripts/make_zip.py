
# Шаг 4 — Скрипт упаковки в ZIP
"""
Create a submission ZIP for Homework 1.

It collects:
- docs/ (README and language_spec.md if present)
- examples/
- lexer/, parser/, main/
- root files: pyproject.toml, setup.cfg, setup.py, README.md (if present)

Result: dist/homework_submission.zip
"""
import os, zipfile, pathlib, sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = PROJECT_ROOT / "dist"
DIST.mkdir(exist_ok=True)

INCLUDE_DIRS = ["docs", "examples", "lexer", "parser", "main"]
INCLUDE_ROOT_FILES = ["pyproject.toml", "setup.cfg", "setup.py", "README.md"]

def add_path(zf: zipfile.ZipFile, path: pathlib.Path):
    if path.is_dir():
        for p in path.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(PROJECT_ROOT))
    elif path.is_file():
        zf.write(path, path.relative_to(PROJECT_ROOT))

def main():
    out_zip = DIST / "homework_submission.zip"
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for d in INCLUDE_DIRS:
            p = PROJECT_ROOT / d
            if p.exists():
                add_path(zf, p)
        for f in INCLUDE_ROOT_FILES:
            p = PROJECT_ROOT / f
            if p.exists():
                add_path(zf, p)
    print(f"[OK] Created: {out_zip}")

if __name__ == "__main__":
    sys.exit(main())
