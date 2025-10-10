from __future__ import annotations
import os, sys, json
from pathlib import Path

# Ensure project root on sys.path (../../ from this file)
_THIS = Path(__file__).resolve()
_PROJ_ROOT = _THIS.parents[2]
if str(_PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJ_ROOT))
from core.positions.position_sizer import SizerConfig, compute_qty_leverage

def main():
    symbol = os.environ.get("SYMBOL", "BTCUSDT")
    wallet_env = os.environ.get("WALLET_USDT")
    if wallet_env is None:
        print(json.dumps({"error": "Set WALLET_USDT env to your live balance."}, indent=2)); sys.exit(2)

    cfg = SizerConfig(
        risk_margin_fraction=float(os.environ.get("RISK_MARGIN_FRACTION", "0.2")),
        preferred_max_leverage=int(os.environ.get("PREFERRED_MAX_LEVERAGE", "10")),
        fee_bps=float(os.environ.get("FEE_BPS", "5")),
        extra_buffer_pct=float(os.environ.get("EXTRA_BUFFER_PCT", "0.02")),
        desired_pos_usdt=float(os.environ["DESIRED_POS_USDT"]) if "DESIRED_POS_USDT" in os.environ else None
    )

    res = compute_qty_leverage(symbol, float(wallet_env), cfg=cfg)
    print(json.dumps({
        "symbol": symbol,
        "qty": res.qty,
        "leverage": res.leverage,
        "min_leverage_needed": res.min_leverage_needed,
        "notional": res.notional,
        "margin_used": res.margin_used,
        "margin_cap": res.margin_cap,
        "price": res.price,
        "lot_step": res.lot_step,
        "min_qty": res.min_qty,
        "min_notional": res.min_notional,
        "notes": res.meta.get("notes"),
    }, indent=2))

if __name__ == "__main__":
    main()

