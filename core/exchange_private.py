from __future__ import annotations
from typing import Dict, Any, List, Optional

def _bool_env(name: str, default: bool=False) -> bool:
    import os
    v = os.getenv(name)
    if v is None: return default
    return v.strip().lower() in {"1","true","yes","y","on"}

def fetch_futures_private() -> Dict[str, Any]:
    """Attempt to read futures balances and positions via python-binance.
    Returns dict with keys: mode, balances, positions, error.
    - mode: 'PRIVATE_OK' if success, 'PUBLIC_ONLY' otherwise.
    """
    import os
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_FAPI_KEY") or os.getenv("API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_FAPI_SECRET") or os.getenv("API_SECRET")
    testnet = _bool_env("BINANCE_TESTNET", False)
    if not api_key or not api_secret:
        return {"mode": "PUBLIC_ONLY", "balances": None, "positions": None, "error": "no_keys"}
    try:
        from binance.client import Client
        cli = Client(api_key, api_secret, testnet=testnet)
        bals = {}
        for b in cli.futures_account_balance():
            try:
                val = float(b.get("balance", 0.0))
                if val > 0:
                    bals[b.get("asset","?")] = val
            except Exception:
                continue
        acct = cli.futures_account()
        pos = [p for p in acct.get("positions", []) if float(p.get("positionAmt", 0.0)) != 0.0]
        return {"mode": "PRIVATE_OK", "balances": bals, "positions": pos, "error": None}
    except Exception as e:
        return {"mode": "PUBLIC_ONLY", "balances": None, "positions": None, "error": str(e)}
