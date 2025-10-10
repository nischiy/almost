# scripts/diagnostics/risk_guard_check.py  (path-robust)
from __future__ import annotations
import os, sys, json
from pathlib import Path
from importlib.machinery import SourceFileLoader

_THIS = Path(__file__).resolve()
_PROJ_ROOT = _THIS.parents[2]
_UTILS_DIR = _PROJ_ROOT / "utils"
_RG_PATH = _UTILS_DIR / "risk_guard.py"

# ensure paths
if str(_PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJ_ROOT))
if str(_UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(_UTILS_DIR))

try:
from core.risk_guard import RiskLimits, RiskState, can_trade  # normal import
except Exception:
    # fallback: load by path
    mod = SourceFileLoader("risk_guard", str(_RG_PATH)).load_module()
    RiskLimits = mod.RiskLimits
    RiskState = mod.RiskState
    can_trade = mod.can_trade

def main():
    limits = RiskLimits(
        max_trades_per_day = int(os.environ.get("RG_MAX_TRADES_PER_DAY", "20")),
        max_loss_streak = int(os.environ.get("RG_MAX_LOSS_STREAK", "5")),
        max_daily_drawdown_usdt = float(os.environ.get("RG_MAX_DD_USDT", "50")),
    )
    st = RiskState(
        trades_today = int(os.environ.get("RG_TRADES_TODAY", "0")),
        loss_streak = int(os.environ.get("RG_LOSS_STREAK", "0")),
        pnl_today_usdt = float(os.environ.get("RG_PNL_TODAY", "0")),
    )
    ok, reason = can_trade(st, limits)
    print(json.dumps({
        "can_trade": ok,
        "reason": reason,
        "state": st.__dict__,
        "limits": limits.__dict__,
    }, indent=2))

if __name__ == "__main__":
    main()

