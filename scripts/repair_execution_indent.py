"""
Repair indentation in app/services/execution.py for ExecutorService.place().
- Removes previous injected '# __PAPER_LOGGING__' block if present.
- Normalizes tabs -> 4 spaces ONLY inside place() body.
- Re-injects a compact, correctly-indented paper CSV logging block at the top of place().
- Idempotent and conservative: edits only the targeted function body.
Run:
    python .\scripts\repair_execution_indent.py
"""
from __future__ import annotations
import re
from pathlib import Path
from datetime import datetime, timezone

TARGET = Path("app")/"services"/"execution.py"

MARKER = "# __PAPER_LOGGING__"
INJECT_LINES = [
    MARKER,
    "try:",
    "    import os as _EP_os",
    "    from pathlib import Path as _EP_Path",
    "    from datetime import datetime as _EP_dt, timezone as _EP_tz",
    "    paper = str(_EP_os.environ.get('PAPER_TRADING','1')).strip().lower() in {'1','true','yes','on'}",
    "    trade_enabled = str(_EP_os.environ.get('TRADE_ENABLED','0')).strip().lower() in {'1','true','yes','on'}",
    "    if paper and not trade_enabled:",
    "        d = _EP_Path('logs') / 'orders' / _EP_dt.now(_EP_tz.utc).strftime('%Y-%m-%d')",
    "        d.mkdir(parents=True, exist_ok=True)",
    "        f = d / 'orders.csv'",
    "        hdr = 'ts,symbol,side,price,sl,tp'",
    "        side = (decision or {}).get('side') if isinstance(decision, dict) else None",
    "        price = (decision or {}).get('price') if isinstance(decision, dict) else None",
    "        sl = (decision or {}).get('sl') if isinstance(decision, dict) else None",
    "        tp = (decision or {}).get('tp') if isinstance(decision, dict) else None",
    "        line = f\"{_EP_dt.now(_EP_tz.utc).isoformat()},{getattr(self,'symbol','?')},{side},{price},{sl},{tp}\"",
    "        if not f.exists():",
    "            f.write_text(hdr + '\\n', encoding='utf-8')",
    "        with f.open('a', encoding='utf-8') as fh:",
    "            fh.write(line + '\\n')",
    "except Exception:",
    "    pass",
    "",
]

def main() -> int:
    if not TARGET.exists():
        print(f"{TARGET} not found; aborting.")
        return 1
    txt = TARGET.read_text(encoding="utf-8", errors="ignore")
    lines = txt.splitlines()

    # Locate class ExecutorService and def place(
    class_idx = None
    for i, ln in enumerate(lines):
        if re.match(r'^\s*class\s+ExecutorService\b', ln):
            class_idx = i
            break
    if class_idx is None:
        print("ExecutorService class not found.")
        return 2

    sig_idx = None
    for i in range(class_idx+1, len(lines)):
        if re.match(r'^\s*def\s+place\s*\(', lines[i]):
            sig_idx = i
            break
        if re.match(r'^\s*class\s+\w+', lines[i]):
            break
    if sig_idx is None:
        print("place() not found under ExecutorService.")
        return 3

    # Determine body indent (indent of first non-empty line after signature)
    body_start = None
    body_indent = ""
    for j in range(sig_idx+1, len(lines)):
        if lines[j].strip() == "":
            continue
        m = re.match(r'^(\s+)', lines[j])
        if m:
            body_start = j
            body_indent = m.group(1)
        else:
            # function with 'pass' on same line unlikely, but handle
            body_start = j
            body_indent = "    "
        break
    if body_start is None:
        print("place() body appears empty.")
        return 4

    # Detect the end of function body: first line that dedents to <= indent of def (indent of signature)
    sig_indent = re.match(r'^(\s*)', lines[sig_idx]).group(1)
    body_end = None
    for k in range(body_start, len(lines)):
        ln = lines[k]
        if ln.strip() == "":
            continue
        cur_indent = re.match(r'^(\s*)', ln).group(1)
        if len(cur_indent) <= len(sig_indent):
            body_end = k
            break
    if body_end is None:
        body_end = len(lines)

    body = lines[body_start:body_end]

    # Normalize tabs to 4 spaces inside body only
    body = [ln.replace("\t", "    ") for ln in body]

    # Remove previous injected block if present (search for MARKER within body)
    if any(MARKER in ln for ln in body):
        new_body = []
        skipping = False
        for ln in body:
            if (MARKER in ln) and (not skipping):
                skipping = True
                continue
            if skipping:
                # stop skipping when dedent to <= body_indent and line not empty
                cur_indent = re.match(r'^(\s*)', ln).group(1)
                if (len(cur_indent) <= len(body_indent) and ln.strip() != ""):
                    skipping = False
                    new_body.append(ln)
                else:
                    continue
            else:
                new_body.append(ln)
        body = new_body

    # Build injection with correct indentation
    inj = [ (body_indent + s) if s else "" for s in INJECT_LINES ]

    # Insert at top of body
    new_body = inj + body

    # Reassemble
    new_lines = lines[:body_start] + new_body + lines[body_end:]
    TARGET.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"Repaired indentation and injected CSV logging in: {TARGET}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
