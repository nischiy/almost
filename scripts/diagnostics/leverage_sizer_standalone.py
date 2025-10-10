#!/usr/bin/env python3
# scripts/diagnostics/leverage_sizer_standalone.py
from __future__ import annotations
import os, json, math, ssl, urllib.request
BASE = os.environ.get("BINANCE_FAPI_BASE", "https://fapi.binance.com")
SYMBOL = os.environ.get("SYMBOL", "BTCUSDT")
WALLET_USDT = os.environ.get("WALLET_USDT")
RISK_MARGIN_FRACTION = float(os.environ.get("RISK_MARGIN_FRACTION", "0.2"))
PREFERRED_MAX_LEVERAGE = int(os.environ.get("PREFERRED_MAX_LEVERAGE", "10"))
FEE_BPS = float(os.environ.get("FEE_BPS", "5"))
EXTRA_BUFFER_PCT = float(os.environ.get("EXTRA_BUFFER_PCT", "0.02"))
DESIRED_POS_USDT = os.environ.get("DESIRED_POS_USDT")
CTX = ssl.create_default_context()
def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "lev-sizer-standalone/1.0"})
    with urllib.request.urlopen(req, timeout=10, context=CTX) as r:
        return json.loads(r.read().decode("utf-8"))
def price(symbol: str) -> float: return float(_get(f"{BASE}/fapi/v1/ticker/price?symbol={symbol}")["price"])
def filters(symbol: str):
    info = _get(f"{BASE}/fapi/v1/exchangeInfo?symbol={symbol}")
    for s in info.get("symbols", []):
        if s.get("symbol") == symbol:
            return {f["filterType"]: f for f in s.get("filters", [])}, s
    return {}, {}
def round_up(x: float, step: float) -> float:
    if step <= 0: return x
    return math.ceil(x / step) * step
def err(msg: str, code: int = 2):
    print(json.dumps({"error": msg}, indent=2)); exit(code)
def main():
    if WALLET_USDT is None: err("WALLET_USDT env is required. Example: set WALLET_USDT=103")
    wallet = float(WALLET_USDT)
    px = price(SYMBOL); f, sym = filters(SYMBOL)
    lot = f.get("LOT_SIZE", {}); step = float(lot.get("stepSize", "0.0")) if lot else 0.0
    min_qty = float(lot.get("minQty", "0.0")) if lot else 0.0
    min_notional = float((f.get("MIN_NOTIONAL") or {}).get("notional", "0.0")) if f else 0.0
    if DESIRED_POS_USDT: target_usdt = max(float(DESIRED_POS_USDT), min_notional)
    else: target_usdt = max(min_notional, min_qty * px)
    qty = round_up(max(target_usdt/px if px>0 else 0.0, min_qty), step) if step>0 else max(target_usdt/px if px>0 else 0.0, min_qty)
    notional = qty * px
    fee_frac = FEE_BPS/10000.0; buf = EXTRA_BUFFER_PCT
    margin_cap = wallet * max(min(RISK_MARGIN_FRACTION, 1.0), 0.0)
    denom = margin_cap / (1.0 + fee_frac + buf) if margin_cap > 0 else 0.0
    min_lev = int(max(1, math.ceil(notional / denom))) if denom > 0 else 999999
    lev = int(max(1, min(max(1, PREFERRED_MAX_LEVERAGE), max(1, min_lev))))

    margin_used = notional / lev * (1.0 + fee_frac + buf)
    print(json.dumps({
        "symbol": SYMBOL, "status": sym.get("status") if sym else None, "price": px,
        "lot_step": step, "min_qty": min_qty, "min_notional": min_notional,
        "wallet_usdt": wallet, "risk_margin_fraction": RISK_MARGIN_FRACTION,
        "target_pos_usdt": target_usdt, "computed_qty": qty, "computed_notional": notional,
        "min_leverage_needed": min_lev, "preferred_max_leverage": PREFERRED_MAX_LEVERAGE,
        "suggested_leverage": lev, "margin_used": margin_used, "margin_cap": margin_cap,
        "margin_ok": margin_used <= margin_cap
    }, indent=2))
if __name__ == "__main__":
    main()
