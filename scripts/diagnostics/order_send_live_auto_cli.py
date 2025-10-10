#!/usr/bin/env python3
# scripts/diagnostics/order_send_live_auto_cli.py
from __future__ import annotations
import os, sys, json, time
from pathlib import Path
from importlib.machinery import SourceFileLoader

_THIS = Path(__file__).resolve()
_PROJ_ROOT = _THIS.parents[2]
_UTILS_DIR = _PROJ_ROOT / "utils"

def _lm(name, path):
    return SourceFileLoader(name, str(path)).load_module()

for p in (_PROJ_ROOT, _UTILS_DIR):
    if str(p) not in sys.path: sys.path.insert(0, str(p))

build_order = _lm("order_adapter", _UTILS_DIR/"order_adapter.py").build_order
place_fix   = _lm("live_bridge",   _UTILS_DIR/"live_bridge.py").place_order_fixed
exit_adp    = _lm("exit_adapter",  _UTILS_DIR/"exit_adapter.py")
auto_pol    = _lm("auto_exit_policy", _UTILS_DIR/"auto_exit_policy.py")

def envf(name: str, default=None, cast=float):
    v = os.environ.get(name)
    if v is None: return default
    try: return cast(v)
    except Exception: return default

def main():
    symbol = os.environ.get("SYMBOL", "BTCUSDT")
    side   = os.environ.get("SIDE", "BUY")
    otype  = os.environ.get("TYPE", "MARKET")
    wallet = envf("WALLET_USDT", None, float)
    if wallet is None:
        print(json.dumps({"error":"Set WALLET_USDT"}, indent=2)); return

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
    prev = outdir / f"preview_{ts}.json"
    prev.write_text(json.dumps(data, indent=2), encoding="utf-8")

    if str(os.environ.get("DRY_RUN_ONLY","1")) != "0":
        abs_path = prev.resolve(); uri = "file:///" + str(abs_path).replace("\\","/")
        print(json.dumps({"result":"preview", "written": str(prev), "written_abs": str(abs_path), "file_uri": uri, "preview": data}, indent=2))
        return

    # LIVE send
    res = place_fix(dict(data["order_payload"]))
    sent = outdir / f"sent_{ts}.json"
    sent.write_text(json.dumps(res, indent=2), encoding="utf-8")
    abs_path = sent.resolve(); uri = "file:///" + str(abs_path).replace("\\","/")

    result = {"result":"sent", "written": str(sent), "written_abs": str(abs_path), "file_uri": uri, **res}

    # AUTO EXITS
    auto = {}
    if auto_pol.should_send_auto_exits():
        # Try to infer entry price: prefer response fill price, else current price from build
        entry_price = None
        # from order response (if any)
        try:
            if isinstance(res.get("order"), dict):
                fills = res["order"].get("avgPrice") or res["order"].get("price")
                if fills: entry_price = float(fills)
        except Exception:
            pass
        if entry_price is None:
            entry_price = envf("ENTRY_PRICE_HINT", None, float)

        sl_p, tp_p = auto_pol.resolve_sl_tp(side, entry_price)
        # fall back to explicit DEFAULT_SL/TP_PRICE if entry_price is None already handled in policy
        sl = sl_p
        tp = tp_p
        auto = exit_adp.send_exits(symbol, side, sl, tp)

    print(json.dumps({**result, "auto_exits": auto}, indent=2))

if __name__ == "__main__":
    main()
