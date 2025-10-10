# scripts/diagnostics/qty_guard_example.py
"""
Dry-run example of guarding qty & leverage before order placement.
- Reads ENV WALLET_USDT (your live balance), SYMBOL, and optional desired pos USDT.
- Prints the corrected qty & suggested leverage. Does not place orders.

Usage:
  $env:WALLET_USDT=103; $env:SYMBOL="BTCUSDT"
  .\.venv\Scripts\python.exe .\scripts\diagnostics\qty_guard_example.py
"""
from __future__ import annotations
import os, sys, json
from pathlib import Path

# robust import
_THIS = Path(__file__).resolve()
_PROJ_ROOT = _THIS.parents[2]
if str(_PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJ_ROOT))
from core.positions.position_sizer import SizerConfig, compute_qty_leverage

def main():
    symbol = os.environ.get("SYMBOL", "BTCUSDT")
    wallet = float(os.environ.get("WALLET_USDT", "0"))
    if wallet <= 0:
        print(json.dumps({"error": "Set WALLET_USDT to your live balance."}, indent=2)); sys.exit(2)

    cfg = SizerConfig(
        risk_margin_fraction=float(os.environ.get("RISK_MARGIN_FRACTION", "0.2")),
        preferred_max_leverage=int(os.environ.get("PREFERRED_MAX_LEVERAGE", "10")),
        desired_pos_usdt=float(os.environ["DESIRED_POS_USDT"]) if "DESIRED_POS_USDT" in os.environ else None
    )
    res = compute_qty_leverage(symbol, wallet, cfg=cfg)
    print(json.dumps({
        "symbol": symbol,
        "computed_qty": res.qty,
        "suggested_leverage": res.leverage,
        "min_leverage_needed": res.min_leverage_needed,
        "notional": res.notional,
        "margin_used": res.margin_used,
        "margin_cap": res.margin_cap,
        "explain": res.meta.get("notes")
    }, indent=2))

if __name__ == "__main__":
    main()

