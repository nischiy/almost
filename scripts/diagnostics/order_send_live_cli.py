#!/usr/bin/env python3
# scripts/diagnostics/order_send_live_cli.py
from __future__ import annotations
import os, sys, json, time
from pathlib import Path
from importlib.machinery import SourceFileLoader

_THIS = Path(__file__).resolve()
_PROJ_ROOT = _THIS.parents[2]
_UTILS_DIR = _PROJ_ROOT / "utils"
_ADAPTER_PATH = _UTILS_DIR / "order_adapter.py"
_BRIDGE_PATH = _UTILS_DIR / "live_bridge.py"

if str(_PROJ_ROOT) not in sys.path: sys.path.insert(0, str(_PROJ_ROOT))
if str(_UTILS_DIR) not in sys.path: sys.path.insert(0, str(_UTILS_DIR))

# Load builders
try:
from app.services.order_adapter import build_order
except Exception:
    build_order = SourceFileLoader("order_adapter", str(_ADAPTER_PATH)).load_module().build_order

try:
from app.services.bridge import place_order_fixed
except Exception:
    place_order_fixed = SourceFileLoader("live_bridge", str(_BRIDGE_PATH)).load_module().place_order_fixed

def envf(name: str, default=None, cast=float):
    v = os.environ.get(name)
    if v is None: return default
    try: return cast(v)
    except Exception: return default

def main():
    symbol = os.environ.get("SYMBOL", "BTCUSDT")
    side = os.environ.get("SIDE", "BUY")
    otype = os.environ.get("TYPE", "MARKET")
    wallet = envf("WALLET_USDT", None, float)
    if wallet is None:
        print(json.dumps({"error": "Set WALLET_USDT"}, indent=2)); return

    data = build_order(
        symbol, side, otype, wallet,
        desired_pos_usdt = envf("DESIRED_POS_USDT", None, float),
        risk_margin_fraction = envf("RISK_MARGIN_FRACTION", 0.2, float),
        preferred_max_leverage = int(envf("PREFERRED_MAX_LEVERAGE", 10, float)),
        price = envf("PRICE", None, float),
        reduce_only = bool(int(os.environ.get("REDUCE_ONLY", "0"))),
        rg_limits = {
            "max_trades_per_day": int(envf("RG_MAX_TRADES_PER_DAY", 20, float)),
            "max_loss_streak": int(envf("RG_MAX_LOSS_STREAK", 5, float)),
            "max_daily_drawdown_usdt": envf("RG_MAX_DD_USDT", 50.0, float),
        },
        rg_state = {
            "trades_today": int(envf("RG_TRADES_TODAY", 0, float)),
            "loss_streak": int(envf("RG_LOSS_STREAK", 0, float)),
            "pnl_today_usdt": envf("RG_PNL_TODAY", 0.0, float),
        }
    )

    ts = int(time.time()*1000)
    day = time.strftime("%Y%m%d")
    outdir = _PROJ_ROOT / "logs" / "orders" / day
    outdir.mkdir(parents=True, exist_ok=True)
    # always write preview
    prev = outdir / f"preview_{ts}.json"
    prev.write_text(json.dumps(data, indent=2), encoding="utf-8")

    if str(os.environ.get("DRY_RUN_ONLY","1")) != "0":
        abs_path = prev.resolve(); uri = "file:///" + str(abs_path).replace("\\","/")
        print(json.dumps({"result":"preview", "written": str(prev), "written_abs": str(abs_path), "file_uri": uri, "preview": data}, indent=2))
        return

    # LIVE: set leverage + send order (no 'leverage' in body)
    res = place_order_fixed(dict(data["order_payload"]))
    sent = outdir / f"sent_{ts}.json"
    sent.write_text(json.dumps(res, indent=2), encoding="utf-8")
    abs_path = sent.resolve(); uri = "file:///" + str(abs_path).replace("\\","/")
    print(json.dumps({"result":"sent", "written": str(sent), "written_abs": str(abs_path), "file_uri": uri, **res}, indent=2))

if __name__ == "__main__":
    main()


