import os, json, sys, traceback, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOTENV = ROOT / ".env"
def _check_shadowing(root: pathlib.Path):
    # Warn if a local 'binance' package could shadow the installed library
    shadow = []
    for p in root.rglob("binance"):
        try:
            if p.is_dir() and (p / "__init__.py").exists():
                sp = str(p)
                if "site-packages" not in sp and ".venv" not in sp and "__pycache__" not in sp:
                    shadow.append(sp)
        except Exception:
            pass
    if shadow:
        print("[WARN] Found local package(s) named 'binance' that may shadow python-binance:")
        for s in shadow:
            print("       -", s)
        print("       Consider renaming those folders (e.g., 'binance_local').")


def _load_dotenv():
    if not DOTENV.exists():
        return
    for line in DOTENV.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line or line.strip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line.strip())
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        # strip surrounding quotes if any
        if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
            v = v[1:-1]
        os.environ.setdefault(k, v)

def main():
    print("=== Preflight LIVE (UM Futures) ===")
    _load_dotenv()
    try:
        from binance.client import Client
    except Exception as e:
        print("[FAIL] python-binance not installed or import error:", e)
        print("      pip install python-binance>=1.0.19  (or: pip install -r requirements.txt)")
        sys.exit(1)

    api_key = os.getenv("API_KEY") or os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("API_SECRET") or os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        print("[FAIL] API keys not found in env (.env): expected API_KEY/API_SECRET (or BINANCE_API_KEY/BINANCE_API_SECRET)")
        sys.exit(2)

    try:
        client = Client(api_key, api_secret)
        print("[OK] Client constructed (keys present)")
    except Exception as e:
        print("[FAIL] Client constructor failed:", e)
        sys.exit(3)

    # Public ping
    try:
        client.ping()
        print("[OK] Public ping")
    except Exception:
        print("[WARN] Public ping failed:")
        traceback.print_exc(limit=1)

    # Futures exchange info
    try:
        info = client.futures_exchange_info()
        syms = {s.get("symbol") for s in info.get("symbols", [])}
        print(f"[OK] futures_exchange_info: {len(syms)} symbols (BTCUSDT={'BTCUSDT' in syms})")
    except Exception:
        print("[WARN] futures_exchange_info failed:")
        traceback.print_exc(limit=1)

    # Private checks
    try:
        bal = client.futures_account_balance()  # List of dicts
        usdt = next((x for x in bal if x.get("asset") == "USDT"), None)
        print(f"[OK] futures_account_balance: USDT={usdt.get('balance') if usdt else 'n/a'}")
    except Exception:
        print("[FAIL] futures_account_balance failed (auth?):")
        traceback.print_exc(limit=1)
        sys.exit(4)

    try:
        acct = client.futures_account()  # Big dict
        total_w = acct.get("totalWalletBalance", "n/a")
        total_upnl = acct.get("totalUnrealizedProfit", "n/a")
        print(f"[OK] futures_account: wallet={total_w}, uPnL={total_upnl}")
    except Exception:
        print("[FAIL] futures_account failed (auth?):")
        traceback.print_exc(limit=1)
        sys.exit(5)

    try:
        pos = client.futures_position_information(symbol="BTCUSDT")
        print(f"[OK] futures_position_information(BTCUSDT): {len(pos)} rows")
    except Exception:
        print("[WARN] futures_position_information failed:")
        traceback.print_exc(limit=1)

    print("=== Preflight DONE ===")

if __name__ == "__main__":
    main()

try:
    _check_shadowing(ROOT)
except Exception:
    pass
