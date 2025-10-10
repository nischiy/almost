#!/usr/bin/env python3
# scripts/diagnostics/order_dry_run.py  (rich output)
from __future__ import annotations
import os, sys, json, time
from pathlib import Path
from importlib.machinery import SourceFileLoader

_THIS = Path(__file__).resolve()
_PROJ_ROOT = _THIS.parents[2]
_UTILS_DIR = _PROJ_ROOT / "utils"

def _load(name: str, path: Path):
    return SourceFileLoader(name, str(path)).load_module()

try:
from core.positions.position_sizer import SizerConfig, compute_qty_leverage
except Exception:
    mod = _load("position_sizer", _UTILS_DIR / "position_sizer.py")
    SizerConfig = mod.SizerConfig
    compute_qty_leverage = mod.compute_qty_leverage

try:
from core.risk_guard import RiskLimits, RiskState, can_trade
except Exception:
    mod = _load("risk_guard", _UTILS_DIR / "risk_guard.py")
    RiskLimits = mod.RiskLimits
    RiskState = mod.RiskState
    can_trade = mod.can_trade

def build_payload(symbol: str, side: str, typ: str, qty: float, price: float|None, leverage: int):
    payload = {
        "symbol": symbol, "side": side.upper(), "type": typ.upper(),
        "quantity": qty, "leverage": leverage, "timeInForce": "GTC",
        "reduceOnly": False, "newClientOrderId": f"dryrun-{int(time.time()*1000)}"
    }
    if typ.upper() == "LIMIT":
        if price is None:
            raise ValueError("PRICE is required for LIMIT orders")
        payload["price"] = float(price)
    return payload

def main():
    symbol = os.environ.get("SYMBOL", "BTCUSDT")
    side = os.environ.get("SIDE", "BUY").upper()
    typ = os.environ.get("TYPE", "MARKET").upper()
    price = float(os.environ["PRICE"]) if (typ == "LIMIT" and "PRICE" in os.environ) else None

    wallet = os.environ.get("WALLET_USDT")
    if wallet is None:
        print(json.dumps({"error": "Set WALLET_USDT env."}, indent=2)); sys.exit(2)
    wallet = float(wallet)

    cfg = SizerConfig(
        risk_margin_fraction=float(os.environ.get("RISK_MARGIN_FRACTION", "0.2")),
        preferred_max_leverage=int(os.environ.get("PREFERRED_MAX_LEVERAGE", "10")),
        desired_pos_usdt=float(os.environ["DESIRED_POS_USDT"]) if "DESIRED_POS_USDT" in os.environ else None
    )
    sized = compute_qty_leverage(symbol, wallet, cfg=cfg)

    limits = RiskLimits(
        max_trades_per_day = int(os.environ.get("RG_MAX_TRADES_PER_DAY", "20")),
        max_loss_streak = int(os.environ.get("RG_MAX_LOSS_STREAK", "5")),
        max_daily_drawdown_usdt = float(os.environ.get("RG_MAX_DD_USDT", "50"))
    )
    st = RiskState(
        trades_today = int(os.environ.get("RG_TRADES_TODAY", "0")),
        loss_streak = int(os.environ.get("RG_LOSS_STREAK", "0")),
        pnl_today_usdt = float(os.environ.get("RG_PNL_TODAY", "0"))
    )
    ok, reason = can_trade(st, limits)

    result = {
        "risk_gate": {"can_trade": ok, "reason": reason, "state": st.__dict__, "limits": limits.__dict__},
        "sizer": {
            "qty": sized.qty, "leverage": sized.leverage, "min_leverage_needed": sized.min_leverage_needed,
            "notional": sized.notional, "margin_used": sized.margin_used, "margin_cap": sized.margin_cap,
            "price": sized.price, "lot_step": sized.lot_step, "min_qty": sized.min_qty, "min_notional": sized.min_notional
        }
    }

    payload = None
    if ok:
        try:
            payload = build_payload(symbol, side, typ, sized.qty, price, sized.leverage)
            result["order_payload"] = payload
        except Exception as e:
            result["order_payload_error"] = str(e)
    else:
        result["order_payload_skipped"] = True

    ts = time.strftime("%Y%m%d")
    outdir = _PROJ_ROOT / "logs" / "orders" / ts
    outdir.mkdir(parents=True, exist_ok=True)
    fname = outdir / f"dryrun_{int(time.time()*1000)}.json"
    fname.write_text(json.dumps(result, indent=2), encoding="utf-8")

    abs_path = fname.resolve()
    file_uri = "file:///" + str(abs_path).replace("\\", "/")
    print(json.dumps({
        "written": str(fname),
        "written_abs": str(abs_path),
        "file_uri": file_uri,
        "can_trade": ok,
        "reason": reason,
        "qty": sized.qty,
        "lev": sized.leverage,
        "type": typ,
        "side": side
    }, indent=2))

if __name__ == "__main__":
    main()


