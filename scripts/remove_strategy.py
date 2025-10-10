from __future__ import annotations
import argparse, sys, ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "strategy.py"

def _imports_strategy(path: Path) -> bool:
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    try:
        tree = ast.parse(src, filename=str(path))
    except Exception:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "strategy":
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == "strategy":
                return True
    return False

def find_real_refs() -> list[Path]:
    refs = []
    for p in ROOT.rglob("*.py"):
        if p == TARGET:
            continue
        if _imports_strategy(p):
            refs.append(p.relative_to(ROOT))
    return refs

def main() -> int:
    ap = argparse.ArgumentParser(description="Safely remove legacy strategy.py if no real imports reference it.")
    ap.add_argument("--force", action="store_true", help="Delete even if references exist")
    args = ap.parse_args()

    refs = find_real_refs()
    if refs and not args.force:
        print("[ABORT] Found imports that reference 'strategy.py':")
        for r in refs:
            print("  -", r)
        print("Fix imports first or run with --force to remove anyway.")
        return 2

    if TARGET.exists():
        TARGET.unlink()
        print("[OK] Deleted:", TARGET)
        (ROOT / "strategy.REMOVED.md").write_text(
            "strategy.py removed. Canonical strategy is core/logic/ema_rsi_atr.py and app/services/signal.py routes to it.\n",
            encoding="utf-8"
        )
        return 0
    else:
        print("[SKIP] strategy.py already absent")
        return 0

if __name__ == "__main__":
    sys.exit(main())
