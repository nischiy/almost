#!/usr/bin/env python3
# scripts/diagnostics/order_send_cli.py  (path-robust)
from __future__ import annotations
import os, sys, json
from pathlib import Path
from importlib.machinery import SourceFileLoader

_THIS = Path(__file__).resolve()
_PROJ_ROOT = _THIS.parents[2]
_UTILS_DIR = _PROJ_ROOT / "utils"
_SENDER_PATH = _UTILS_DIR / "sender_adapter.py"

# ensure paths
if str(_PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJ_ROOT))
if str(_UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(_UTILS_DIR))

try:
from app.services.notifications import place_order_via_rest  # normal import
except Exception:
    mod = SourceFileLoader("sender_adapter", str(_SENDER_PATH)).load_module()
    place_order_via_rest = mod.place_order_via_rest

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

    data = place_order_via_rest(
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
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()

