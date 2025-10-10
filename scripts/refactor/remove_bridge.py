
#!/usr/bin/env python3
import argparse, os, re, sys, json, shutil, io
from pathlib import Path

PAT_IMPORTS = [
    re.compile(r'(?m)^\s*from\s+utils\.live_bridge\s+import\s+run_once\s*(?:as\s+\w+)?\s*$'),
    re.compile(r'(?m)^\s*from\s+app\.services\.bridge\s+import\s+run_once\s*(?:as\s+\w+)?\s*$'),
    re.compile(r'(?m)^\s*import\s+utils\.live_bridge\s+as\s+\w+\s*$'),
    re.compile(r'(?m)^\s*import\s+app\.services\.bridge\s+as\s+\w+\s*$'),
    re.compile(r'(?m)^\s*import\s+utils\.live_bridge\s*$'),
    re.compile(r'(?m)^\s*import\s+app\.services\.bridge\s*$'),
]

# Replace call patterns:
# 1) var = run_once(md, sig, exe, symbol, interval, params)
RE_ASSIGN_DIRECT = re.compile(r'(?m)^(?P<indent>\s*)(?P<lhs>\w+)\s*=\s*run_once\((?P<args>[^)]*)\)\s*$')
RE_CALL_DIRECT   = re.compile(r'(?m)^(?P<indent>\s*)run_once\((?P<args>[^)]*)\)\s*$')

# 2) var = bridge.run_once(...), bare bridge.run_once(...)
RE_ASSIGN_BRIDGE = re.compile(r'(?m)^(?P<indent>\s*)(?P<lhs>\w+)\s*=\s*(?P<mod>\w+)\.run_once\((?P<args>[^)]*)\)\s*$')
RE_CALL_BRIDGE   = re.compile(r'(?m)^(?P<indent>\s*)(?P<mod>\w+)\.run_once\((?P<args>[^)]*)\)\s*$')

def inline_block(indent: str, lhs: str|None, args: str) -> str:
    # Expect args order: md, sig, exe, symbol, interval, params
    parts = [a.strip() for a in args.split(",")]
    if len(parts) < 6:
        # leave untouched if unexpected signature
        return None
    md, sig, exe, symbol, interval, params = parts[:6]
    lines = []
    lines.append(f"{indent}# BRIDGE_REMOVED: inlined fetch -> decide -> execute")
    lines.append(f"{indent}df = {md}.get_klines({symbol}, {interval}, limit=200)")
    lines.append(f"{indent}decision = {sig}.decide(df, {params})")
    lines.append(f"{indent}if decision.get('action') in ('BUY','SELL','LONG','SHORT'):",)
    lines.append(f"{indent}    {exe}.place(decision)")
    if lhs:
        lines.append(f"{indent}{lhs} = decision")
    return "\n".join(lines)

def process_text(text: str) -> tuple[str, bool]:
    changed = False
    orig = text

    # Remove import lines
    for pat in PAT_IMPORTS:
        text_new = pat.sub("", text)
        if text_new != text:
            text = text_new
            changed = True

    # Replace assignment call forms first (to avoid double-handling)
    def repl_assign_direct(m):
        block = inline_block(m.group("indent"), m.group("lhs"), m.group("args"))
        return block if block else m.group(0)
    def repl_call_direct(m):
        block = inline_block(m.group("indent"), None, m.group("args"))
        return block if block else m.group(0)
    def repl_assign_bridge(m):
        block = inline_block(m.group("indent"), m.group("lhs"), m.group("args"))
        return block if block else m.group(0)
    def repl_call_bridge(m):
        block = inline_block(m.group("indent"), None, m.group("args"))
        return block if block else m.group(0)

    for pat, fn in [(RE_ASSIGN_DIRECT,repl_assign_direct),
                    (RE_CALL_DIRECT,repl_call_direct),
                    (RE_ASSIGN_BRIDGE,repl_assign_bridge),
                    (RE_CALL_BRIDGE,repl_call_bridge)]:
        text_new = pat.sub(fn, text)
        if text_new != text:
            text = text_new
            changed = True

    # Tidy multiple blank lines caused by removed imports
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text, changed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--whatif", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)

    # 1) Patch all .py files (except .venv)
    patched = []
    for p in root.rglob("*.py"):
        if ".venv" in p.parts: 
            continue
        try:
            s = p.read_text(encoding="utf-8")
        except Exception:
            continue
        new_s, changed = process_text(s)
        if changed:
            if args.whatif:
                print(f"[WhatIf] PATCH {p}")
            else:
                p.write_text(new_s, encoding="utf-8")
                print(f"[PATCH] {p}")
            patched.append(str(p))

    # 2) Remove bridge modules if present
    candidates = [
        root / "utils" / "live_bridge.py",
        root / "app" / "services" / "bridge.py",
    ]
    removed = []
    for c in candidates:
        if c.exists():
            if args.whatif:
                print(f"[WhatIf] DEL {c}")
            else:
                c.unlink()
                print(f"[DEL] {c}")
            removed.append(str(c))

    # 3) Remove empty utils dir if became empty
    udir = root / "utils"
    try:
        if udir.exists() and not any(udir.iterdir()):
            if args.whatif:
                print(f"[WhatIf] RMDIR {udir}")
            else:
                udir.rmdir()
                print(f"[RMDIR] {udir}")
    except Exception:
        pass

    # 4) Summary
    print(json.dumps({
        "patched": patched,
        "removed": removed
    }, indent=2))

if __name__ == "__main__":
    sys.exit(main())
