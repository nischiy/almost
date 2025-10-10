# -*- coding: utf-8 -*-
"""
strip_bom.py — видаляє UTF-8 BOM з усіх .py-файлів у дереві проекту.
Використання:
  python scripts/maintenance/strip_bom.py --check
  python scripts/maintenance/strip_bom.py --write
Опції:
  --root PATH     Корінь (за замовч. поточна тека)
  --ext .py,.pyi  Розширення через кому (дефолт: .py)
Exit code:
  0 — OK (нічого не знайдено/успішно виправлено), 1 — знайдені BOM у режимі --check, 2 — помилка.
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path

BOM = b'\xef\xbb\xbf'

def has_bom(data: bytes) -> bool:
    return data.startswith(BOM)

def process_file(p: Path, write: bool) -> bool:
    data = p.read_bytes()
    if has_bom(data):
        if write:
            p.write_bytes(data[len(BOM):])
            print(f"[FIXED] {p}")
        else:
            print(f"[BOM]   {p}")
        return True
    return False

def walk(root: Path, exts: set[str]) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in exts:
            files.append(path)
    return files

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, default=".")
    ap.add_argument("--ext", type=str, default=".py")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    exts = set([e.strip().lower() if e.strip().startswith(".") else "."+e.strip().lower()
                for e in args.ext.split(",") if e.strip()])
    targets = walk(root, exts)
    found = 0
    for p in targets:
        try:
            if process_file(p, write=args.write):
                found += 1
        except Exception as e:
            print(f"[ERROR] {p}: {e}", file=sys.stderr)
            return 2

    if args.check:
        if found > 0:
            print(f"[SUMMARY] Found {found} file(s) with BOM.")
            return 1
        print("[SUMMARY] No BOM found.")
        return 0
    else:
        print(f"[SUMMARY] Fixed {found} file(s).")
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
