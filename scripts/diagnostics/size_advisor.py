#!/usr/bin/env python3
# scripts/diagnostics/size_advisor.py
from __future__ import annotations
import os, json, math, ssl, urllib.request
BASE = os.environ.get("BINANCE_FAPI_BASE", "https://fapi.binance.com")
SYMBOL = os.environ.get("SYMBOL", "BTCUSDT")
TARGET_USDT = float(os.environ.get("DESIRED_POS_USDT", "120.0"))
CTX = ssl.create_default_context()
def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "size-advisor/1.0"})
    with urllib.request.urlopen(req, timeout=10, context=CTX) as r:
        return json.loads(r.read().decode("utf-8"))
def price(symbol: str) -> float:
    return float(_get(f"{BASE}/fapi/v1/ticker/price?symbol={symbol}")["price"])
def filters(symbol: str):
    info = _get(f"{BASE}/fapi/v1/exchangeInfo?symbol={symbol}")
    for s in info.get("symbols", []):
        if s.get("symbol") == symbol:
            return {f["filterType"]: f for f in s.get("filters", [])}
    return {}
def round_up(x: float, step: float) -> float:
    if step <= 0: return x
    return math.ceil(x / step) * step
def main():
    px = price(SYMBOL)
    f = filters(SYMBOL)
    lot = f.get("LOT_SIZE", {})
    step = float(lot.get("stepSize", "0.0")) if lot else 0.0
    min_qty = float(lot.get("minQty", "0.0")) if lot else 0.0
    min_notional = float((f.get("MIN_NOTIONAL") or {}).get("notional", "0.0")) if f else 0.0
    q_target = TARGET_USDT / px if px > 0 else 0.0
    q = max(q_target, min_qty, (min_notional/px if px>0 else 0.0))
    q = round_up(q, step) if step > 0 else q
    final_usdt = q * px
    print(json.dumps({
        "symbol": SYMBOL, "price": px, "step_size": step, "min_qty": min_qty,
        "min_notional": min_notional, "desired_pos_usdt": TARGET_USDT,
        "computed_qty": q, "computed_pos_usdt": final_usdt
    }, indent=2))
if __name__ == "__main__":
    main()
