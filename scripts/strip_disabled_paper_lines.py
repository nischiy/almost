"""
Remove lines marked with '# disabled: paper_trades.csv artifact' and the immediate
next commented line that holds the original code. Operates repo-wide, excluding .venv/logs/__pycache__.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def skip(p: Path) -> bool:
    s = str(p)
    return any(seg in s for seg in (str(ROOT / ".venv"), str(ROOT / "logs"), "__pycache__"))

changed = 0
for f in ROOT.rglob("*.py"):
    if skip(f):
        continue
    text = f.read_text(encoding="utf-8", errors="ignore").splitlines()
    out = []
    i = 0
    modified = False
    while i < len(text):
        line = text[i]
        if line.strip() == "# disabled: paper_trades.csv artifact":
            modified = True
            # skip this marker line
            i += 1
            # optionally skip the next line if it's a single-line comment that followed the disabled code
            if i < len(text) and text[i].lstrip().startswith("# "):
                i += 1
            continue
        out.append(line)
        i += 1
    if modified:
        f.write_text("\n".join(out) + ("\n" if (out and not out[-1].endswith("\n")) else ""), encoding="utf-8")
        changed += 1
        print(f"[CLEANED] {f}")
print(f"[DONE] Cleaned files: {changed}")
