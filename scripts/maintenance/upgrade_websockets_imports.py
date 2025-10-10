# -*- coding: utf-8 -*-
# Safe upgrader for websockets imports to 14/15 API.
# - Scans repo for .py files in typical roots.
# - Reports planned changes (DryRun default).
# - With --apply: writes changes, keeping .bak backups.
# - Only rewrites explicit import forms known to be safe:
#     from websockets.client import X      -> from websockets.asyncio.client import X
#     from websockets.server import X      -> from websockets.asyncio.server import X
#     from websockets.legacy.client import X -> from websockets.asyncio.client import X
#     from websockets.legacy.server import X -> from websockets.asyncio.server import X
#     import websockets.legacy.client as A -> import websockets.asyncio.client as A
#     import websockets.legacy.server as A -> import websockets.asyncio.server as A
#     import websockets.client as A        -> import websockets.asyncio.client as A
#     import websockets.server as A        -> import websockets.asyncio.server as A
# - Leaves 'from websockets import connect, serve' як є (це вже ок для 14+).
# - Не чіпає неоднозначні патерни; про них повідомляє.
from __future__ import annotations
import argparse, re, sys
from pathlib import Path

ROOTS = ["app", "core", "scripts", "tools", "tests"]

REPLACERS = [
    # from ... import ...
    (re.compile(r"^\s*from\s+websockets\.legacy\.client\s+import\s+(.*)$"), r"from websockets.asyncio.client import \1"),
    (re.compile(r"^\s*from\s+websockets\.legacy\.server\s+import\s+(.*)$"), r"from websockets.asyncio.server import \1"),
    (re.compile(r"^\s*from\s+websockets\.client\s+import\s+(.*)$"),         r"from websockets.asyncio.client import \1"),
    (re.compile(r"^\s*from\s+websockets\.server\s+import\s+(.*)$"),         r"from websockets.asyncio.server import \1"),
    # import ... as ...
    (re.compile(r"^\s*import\s+websockets\.legacy\.client\s+as\s+(\w+)\s*$"), r"import websockets.asyncio.client as \1"),
    (re.compile(r"^\s*import\s+websockets\.legacy\.server\s+as\s+(\w+)\s*$"), r"import websockets.asyncio.server as \1"),
    (re.compile(r"^\s*import\s+websockets\.client\s+as\s+(\w+)\s*$"),        r"import websockets.asyncio.client as \1"),
    (re.compile(r"^\s*import\s+websockets\.server\s+as\s+(\w+)\s*$"),        r"import websockets.asyncio.server as \1"),
]

# Patterns we flag but НЕ змінюємо автоматично
FLAG_ONLY = [
    re.compile(r"^\s*import\s+websockets\.client\s*$"),
    re.compile(r"^\s*import\s+websockets\.server\s*$"),
    re.compile(r"^\s*import\s+websockets\.legacy\.(client|server)\s*$"),
]

def iter_py_files(project_root: Path):
    for root in ROOTS:
        p = project_root / root
        if not p.is_dir():
            continue
        for f in p.rglob("*.py"):
            s = str(f)
            if any(x in s for x in (".venv", ".git", "__pycache__", "site-packages")):
                continue
            yield f

def transform_lines(lines):
    changed = False
    flagged = []
    out = []
    for ln, line in enumerate(lines, 1):
        orig = line
        for rx, rep in REPLACERS:
            if rx.search(line):
                line = rx.sub(rep, line)
                changed = True
                break
        else:
            for flag_rx in FLAG_ONLY:
                if flag_rx.search(line):
                    flagged.append((ln, orig.rstrip("\n")))
                    break
        out.append(line)
    return changed, flagged, out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes in-place with .bak backups")
    ap.add_argument("--project-root", default=".", help="Repo root (default: current dir)")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    total_changed = 0
    total_flagged = 0

    for py in iter_py_files(root):
        txt = py.read_text(encoding="utf-8", errors="ignore").splitlines(True)
        changed, flagged, out = transform_lines(txt)
        if flagged:
            print(f"[FLAG] {py} has ambiguous imports:")
            for ln, raw in flagged:
                print(f"       L{ln}: {raw}")
            total_flagged += len(flagged)
        if changed:
            total_changed += 1
            print(f"[PLAN] rewrite {py}")
            if args.apply:
                bak = py.with_suffix(py.suffix + ".bak")
                if not bak.exists():
                    bak.write_text("".join(txt), encoding="utf-8")
                py.write_text("".join(out), encoding="utf-8")
                print(f"[OK]    wrote {py} (backup: {bak.name})")
            else:
                print(f"[DRY]   would write {py}")

    print(f"[SUMMARY] changed_candidates={total_changed} flagged_lines={total_flagged} apply={args.apply}")

if __name__ == "__main__":
    import sys
    sys.exit(main())
