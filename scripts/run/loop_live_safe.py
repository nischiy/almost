#!/usr/bin/env python3
# scripts/run/loop_live_safe.py
"""
Minimal safe live loop (opt-in):
- Respects TRADE_ENABLED=1, PAPER_TRADING=0, DRY_RUN_ONLY=0
- Max trades/day via RG_MAX_TRADES_PER_DAY (default 20)
- Side/Type from ENV: LOOP_SIDE (BUY/SELL), LOOP_TYPE (MARKET/LIMIT), optional LOOP_PRICE
- Optional exits per trade: LOOP_SL, LOOP_TP
- Sleeps LOOP_SLEEP_S between iterations (default 10s)

This is intentionally simple and conservative. Prefer integrating order_service.place(...) in your own loop.
"""
from __future__ import annotations
import os, sys, time, json
from pathlib import Path
from importlib.machinery import SourceFileLoader

_THIS = Path(__file__).resolve()
_PROJ_ROOT = _THIS.parents[2]
_UTILS_DIR = _PROJ_ROOT / "utils"
_SERVICE_PATH = _UTILS_DIR / "order_service.py"
_EXIT_PATH = _UTILS_DIR / "exit_adapter.py"

if str(_PROJ_ROOT) not in sys.path: sys.path.insert(0, str(_PROJ_ROOT))
if str(_UTILS_DIR) not in sys.path: sys.path.insert(0, str(_UTILS_DIR))

def _envf(name: str, default=None, cast=float):
    v = os.environ.get(name)
    if v is None: return default
    try: return cast(v)
    except Exception: return default

try:
from app.services.order_service import place
except Exception:
    place = SourceFileLoader("order_service", str(_SERVICE_PATH)).load_module().place

try:
from app.services.exit_adapter import send_exits
except Exception:
    send_exits = SourceFileLoader("exit_adapter", str(_EXIT_PATH)).load_module().send_exits

def main():
    if os.environ.get("TRADE_ENABLED","0") != "1": print(json.dumps({"skip":"TRADE_ENABLED!=1"})); return
    if os.environ.get("PAPER_TRADING","0") != "0": print(json.dumps({"skip":"PAPER_TRADING!=0"})); return
    if os.environ.get("DRY_RUN_ONLY","1") != "0": print(json.dumps({"skip":"DRY_RUN_ONLY!=0"})); return

    symbol = os.environ.get("SYMBOL","BTCUSDT")
    max_trades = int(_envf("RG_MAX_TRADES_PER_DAY", 20, float))
    sleep_s = int(_envf("LOOP_SLEEP_S", 10, float))
    side = os.environ.get("LOOP_SIDE", "BUY")
    typ = os.environ.get("LOOP_TYPE", "MARKET")
    price = _envf("LOOP_PRICE", None, float)
    sl = _envf("LOOP_SL", None, float)
    tp = _envf("LOOP_TP", None, float)

    trades = 0
    while trades < max_trades:
        res = place(symbol, side, typ, price=price,
                    risk_margin_fraction=_envf("RISK_MARGIN_FRACTION", 0.2, float),
                    preferred_max_leverage=int(_envf("PREFERRED_MAX_LEVERAGE", 10, float)))
        print(json.dumps({"entry": res.get("result"), "written": res.get("written"), "file_uri": res.get("file_uri")}, indent=2))
        if sl or tp:
            os.environ["SIDE"] = side  # entry side for exit adapter
            if sl: os.environ["SL_PRICE"] = str(sl)
            if tp: os.environ["TP_PRICE"] = str(tp)
            os.environ["SEND_EXITS"] = "1"
            ex = send_exits(symbol, side, sl, tp)
            print(json.dumps({"exits": ex.get("result","preview"), **ex}, indent=2))
        trades += 1
        time.sleep(sleep_s)

if __name__ == "__main__":
    main()


