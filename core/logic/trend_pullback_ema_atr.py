from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from core.logic.indicators import atr, ema, ensure_ohlc, required_history


def _insufficient_history(df: pd.DataFrame, needed: int) -> Dict[str, Any]:
    price = None
    try:
        _, _, close = ensure_ohlc(df)
        price = float(close.iloc[-1])
    except Exception:
        price = None
    return {
        "action": "HOLD",
        "side": "HOLD",
        "reason": "insufficient_history",
        "reasons": [f"need_{needed}_candles", f"have_{len(df)}_candles"],
        "price": price,
        "indicators": {"required_history": needed},
        "sl": None,
        "tp": None,
    }


def generate_signal(df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
    if df is None or df.empty:
        return {"action": "HOLD", "side": "HOLD", "reason": "empty_df", "reasons": ["empty_df"], "price": None, "indicators": {}, "sl": None, "tp": None}

    ema_fast = int(params.get("ema_fast", 50))
    ema_slow = int(params.get("ema_slow", 200))
    atr_period = int(params.get("atr_period", 14))
    pullback_k = float(params.get("pullback_atr", 1.0))
    sl_k = float(params.get("sl_atr", 1.5))
    tp_k = float(params.get("tp_atr", 2.0))

    needed = required_history(ema_fast, ema_slow, atr_period)
    if len(df) < needed:
        return _insufficient_history(df, needed)

    high, low, close = ensure_ohlc(df)
    ema_fast_series = ema(close, ema_fast)
    ema_slow_series = ema(close, ema_slow)
    atr_series = atr(df, atr_period)

    price = float(close.iloc[-1])
    ema_fast_val = float(ema_fast_series.iloc[-1])
    ema_slow_val = float(ema_slow_series.iloc[-1])
    atr_val = float(atr_series.iloc[-1]) if not atr_series.empty else None
    low_val = float(low.iloc[-1])
    high_val = float(high.iloc[-1])

    reasons = []
    trend_up = ema_fast_val > ema_slow_val
    trend_down = ema_fast_val < ema_slow_val
    reasons.append("trend_up" if trend_up else "trend_down" if trend_down else "trend_flat")

    pullback_long = False
    pullback_short = False
    if atr_val:
        pullback_long = low_val < ema_fast_val and (ema_fast_val - low_val) <= pullback_k * atr_val
        pullback_short = high_val > ema_fast_val and (high_val - ema_fast_val) <= pullback_k * atr_val

    trigger_long = pullback_long and price > ema_fast_val
    trigger_short = pullback_short and price < ema_fast_val

    reasons.append("pullback_long" if pullback_long else "no_pullback_long")
    reasons.append("pullback_short" if pullback_short else "no_pullback_short")
    reasons.append("trigger_long" if trigger_long else "no_trigger_long")
    reasons.append("trigger_short" if trigger_short else "no_trigger_short")

    if trend_up and trigger_long:
        action = "BUY"
        primary_reason = "trend_pullback_long"
    elif trend_down and trigger_short:
        action = "SELL"
        primary_reason = "trend_pullback_short"
    else:
        action = "HOLD"
        primary_reason = "no_signal"

    decision: Dict[str, Any] = {
        "action": action,
        "side": action,
        "reason": primary_reason,
        "reasons": reasons,
        "price": price,
        "ema_fast": ema_fast_val,
        "ema_slow": ema_slow_val,
        "atr": atr_val,
        "indicators": {
            "ema_fast": ema_fast_val,
            "ema_slow": ema_slow_val,
            "atr": atr_val,
            "pullback_k": pullback_k,
            "low": low_val,
            "high": high_val,
        },
        "sl": None,
        "tp": None,
    }

    if atr_val and action in {"BUY", "SELL"}:
        if action == "BUY":
            decision["sl"] = price - sl_k * atr_val
            decision["tp"] = price + tp_k * atr_val
        else:
            decision["sl"] = price + sl_k * atr_val
            decision["tp"] = price - tp_k * atr_val

    return decision


class Strategy:
    @staticmethod
    def decide(*args, **kwargs):
        return generate_signal(*args, **kwargs)


def decide(*args, **kwargs):
    return generate_signal(*args, **kwargs)


def signal(*args, **kwargs):
    return decide(*args, **kwargs)
