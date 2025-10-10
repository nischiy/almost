import os, sys, traceback

def main():
    print("=== python-binance import check ===")
    try:
        from binance.client import Client  # type: ignore
        print("[OK] Imported binance.client.Client")
    except Exception as e:
        print("[FAIL] Cannot import python-binance. Install with: pip install python-binance>=1.0.19")
        print("Error:", e)
        sys.exit(1)

    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("API_SECRET")
    if not api_key or not api_secret:
        print("[WARN] API keys not found in env (BINANCE_API_KEY/BINANCE_API_SECRET or API_KEY/API_SECRET).")
        print("       Live client will not authenticate. Set your .env accordingly.")
        # do not exit; just continue to construct unauthenticated client for ping

    try:
        client = Client(api_key or "", api_secret or "")
        print("[OK] Client constructed")
    except Exception as e:
        print("[FAIL] Client constructor failed:", e)
        sys.exit(1)

    # Try a lightweight public call
    try:
        pong = client.ping()
        print("[OK] ping():", pong)
    except Exception:
        print("[WARN] ping() failed; public connectivity issue or client misconfig:")
        traceback.print_exc(limit=1)

    # Try exchangeInfo for BTCUSDT (public)
    try:
        info = client.futures_exchange_info()
        syms = {s.get("symbol") for s in info.get("symbols", [])}
        msg = "[OK] futures_exchange_info(): BTCUSDT present" if "BTCUSDT" in syms else "[WARN] BTCUSDT not in symbols"
        print(msg, f"({len(syms)} symbols)")
    except Exception:
        print("[WARN] futures_exchange_info() failed:")
        traceback.print_exc(limit=1)

    print("=== Done ===")

if __name__ == "__main__":
    main()
