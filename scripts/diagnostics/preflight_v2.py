#!/usr/bin/env python3
# scripts/diagnostics/preflight_v2.py
from __future__ import annotations
import os, sys, time, math, json, datetime as dt, urllib.request, ssl

BINANCE_FAPI = os.environ.get("BINANCE_FAPI_BASE", "https://fapi.binance.com")
SYMBOL = os.environ.get("SYMBOL", "BTCUSDT")
INTERVAL = os.environ.get("INTERVAL", "1m")
TIMEOUT = int(os.environ.get("PREFLIGHT_TIMEOUT_SEC", "10"))
MAX_DRIFT_MS = int(os.environ.get("PREFLIGHT_MAX_DRIFT_MS", "1500"))
SSL_CTX = ssl.create_default_context()

def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "preflight-v2/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=SSL_CTX) as r:
        return json.loads(r.read().decode("utf-8"))

def server_time_ms():
    return int(_get(f"{BINANCE_FAPI}/fapi/v1/time")["serverTime"])

def ping_ok():
    try:
        _ = _get(f"{BINANCE_FAPI}/fapi/v1/ping")
        return True, None
    except Exception as e:
        return False, str(e)

def exchange_info(symbol: str):
    return _get(f"{BINANCE_FAPI}/fapi/v1/exchangeInfo?symbol={symbol}")

def price(symbol: str):
    return float(_get(f"{BINANCE_FAPI}/fapi/v1/ticker/price?symbol={symbol}")["price"])

def filters_map(ex_info: dict, symbol: str):
    for s in ex_info.get("symbols", []):
        if s.get("symbol") == symbol:
            return {f["filterType"]: f for f in s.get("filters", [])}, s
    return {}, {}

def now_ms(): return int(time.time() * 1000)
def human_ts(ms: int): return dt.datetime.utcfromtimestamp(ms/1000).isoformat() + "Z"

def check_time_drift():
    srv = server_time_ms(); loc = now_ms(); drift = abs(srv - loc)
    return drift, srv, loc

def check_symbol_filters(fs: dict, px: float):
    out = {}
    lot = fs.get("LOT_SIZE", {})
    step_size = float(lot.get("stepSize", "0.0")) if lot else 0.0
    min_qty = float(lot.get("minQty", "0.0")) if lot else 0.0
    notional = fs.get("MIN_NOTIONAL", {})
    min_notional = float(notional.get("notional", "0.0")) if notional else 0.0

    def round_up(x, step):
        import math
        if step <= 0: return x
        return math.ceil(x / step) * step

    qty_for_notional = (min_notional / px) if px > 0 else 0.0
    min_qty_all = max(min_qty, qty_for_notional)
    rounded_qty = round_up(min_qty_all, step_size) if step_size > 0 else min_qty_all

    out["price"] = px
    out["step_size"] = step_size
    out["min_qty"] = min_qty
    out["min_notional"] = min_notional
    out["min_qty_satisfying_all"] = rounded_qty
    out["est_min_pos_usdt"] = rounded_qty * px
    return out

def main():
    ok, err = ping_ok()
    report = {"ping_ok": ok, "ping_err": err}
    drift, srv, loc = check_time_drift()
    report["time"] = {"server": srv, "local": loc, "drift_ms": drift, "drift_ok": drift <= MAX_DRIFT_MS}
    try:
        ex = exchange_info(SYMBOL)
        fs, sym = filters_map(ex, SYMBOL)
        px = price(SYMBOL)
        fstats = check_symbol_filters(fs, px)
    except Exception as e:
        report["exchange_info_err"] = str(e)
        fs, sym, fstats = {}, {}, {}

    report["symbol"] = SYMBOL
    report["filters_found"] = list(fs.keys()) if fs else []
    report["symbol_status"] = sym.get("status") if sym else None
    report["qty_constraints"] = fstats
    print(json.dumps(report, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
