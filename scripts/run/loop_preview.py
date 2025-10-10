#!/usr/bin/env python3
# scripts/run/loop_preview.py
"""
Minimal loop that demonstrates how to call the centralized order service.
- Safe: DRY_RUN_ONLY=1 by default
- Strategy stub: alternates BUY MARKET then SELL LIMIT (price = px*1.02) every iteration
- Sleeps between iterations
"""
from __future__ import annotations
import os, sys, time, json
from pathlib import Path
from importlib.machinery import SourceFileLoader

_THIS = Path(__file__).resolve()
_PROJ_ROOT = _THIS.parents[2]
_UTILS_DIR = _PROJ_ROOT / "utils"
_SERVICE_PATH = _UTILS_DIR / "order_service.py"

if str(_PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJ_ROOT))
if str(_UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(_UTILS_DIR))

try:
from app.services.order_service import place
except Exception:
    mod = SourceFileLoader("order_service", str(_SERVICE_PATH)).load_module()
    place = mod.place

def _envf(name: str, default=None, cast=float):
    v = os.environ.get(name)
    if v is None: return default
    try: return cast(v)
    except Exception: return default

def main():
    symbol = os.environ.get("SYMBOL", "BTCUSDT")
    iterations = int(_envf("LOOP_ITERS", 2, float))
    sleep_s = int(_envf("LOOP_SLEEP_S", 5, float))

    # Simple alternator strategy for demo
    for i in range(iterations):
        side, typ, price = ("BUY", "MARKET", None) if i % 2 == 0 else ("SELL", "LIMIT", _envf("DEMO_LIMIT_PRICE", None, float))
        res = place(
            symbol, side, typ,
            price=price,
            risk_margin_fraction=_envf("RISK_MARGIN_FRACTION", 0.2, float),
            preferred_max_leverage=int(_envf("PREFERRED_MAX_LEVERAGE", 10, float)),
        )
        print(json.dumps({"iter": i+1, "result": res.get("result"), "written": res.get("written"), "file_uri": res.get("file_uri")}, indent=2))
        time.sleep(sleep_s)

if __name__ == "__main__":
    main()

