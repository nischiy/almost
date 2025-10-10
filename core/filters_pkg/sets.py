from __future__ import annotations
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timezone

from core.filters.gates import (
    GateConfig,
    session_gate,
    atr_percentile_gate,
    htf_trend_gate,
)
from core.filters import gates as _G  # for _load_snapshot_df()


# --- extra primitive for weekday check (kept here to avoid export from gates) ---
def _weekday_gate(now_utc: datetime, cfg: GateConfig) -> Tuple[bool, str]:
    try:
        allowed = {int(x.strip()) for x in cfg.weekdays.split(",") if x.strip()}
    except Exception:
        allowed = {1,2,3,4,5}
    wd = ((now_utc.weekday() + 1 - 1) % 7) + 1  # 1..7
    return (wd in allowed), f"weekday:{wd} in {sorted(allowed)}"


# --- presets (compositions of gates) ---
PRESET_SESSION_ONLY = ["weekday", "session"]
PRESET_VOLATILITY_ONLY = ["atr"]
PRESET_TREND_ONLY = ["trend"]
PRESET_SWING_SAFE = ["weekday", "session", "atr", "trend"]

PRESETS: Dict[str, List[str]] = {
    "SESSION_ONLY": PRESET_SESSION_ONLY,
    "VOLATILITY_ONLY": PRESET_VOLATILITY_ONLY,
    "TREND_ONLY": PRESET_TREND_ONLY,
    "SWING_SAFE": PRESET_SWING_SAFE,
}


def evaluate_preset(side: str,
                    preset: str = "SWING_SAFE",
                    now_utc: Optional[datetime] = None,
                    cfg: Optional[GateConfig] = None) -> Tuple[bool, List[str]]:
    """Evaluate a predefined set of gates and return (ok, messages).
    """
    now_utc = now_utc or datetime.now(timezone.utc)
    cfg = cfg or GateConfig()
    df = _G._load_snapshot_df()  # may be None if no snapshots

    order = PRESETS.get(preset.upper())
    if not order:
        raise KeyError(f"Unknown preset: {preset}. Available: {list(PRESETS)}")

    oks: List[bool] = []
    msgs: List[str] = []

    for gate in order:
        if gate == "weekday":
            ok, msg = _weekday_gate(now_utc, cfg)
        elif gate == "session":
            ok, msg = session_gate(now_utc, cfg)
        elif gate == "atr":
            ok, msg = atr_percentile_gate(df, cfg)
        elif gate == "trend":
            ok, msg = htf_trend_gate(df, side, cfg)
        else:
            raise ValueError(f"Unsupported gate: {gate}")
        oks.append(ok); msgs.append(msg)

    return all(oks), msgs
