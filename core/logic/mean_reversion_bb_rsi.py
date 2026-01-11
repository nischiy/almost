from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from core.logic.indicators import (
    bollinger_bands,
    ema,
    ensure_ohlc,
    required_history,
    rsi,
)


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

    bb_period = int(params.get("bb_period", 20))
    bb_std = float(params.get("bb_std", 2.0))
    rsi_period = int(params.get("rsi_period", 14))
    rsi_os = float(params.get("rsi_os", 30.0))
    rsi_ob = float(params.get("rsi_ob", 70.0))
    use_ema_filter = bool(params.get("use_ema200_filter", False))
    ema_period = int(params.get("ema_filter_period", 200))

    needed = required_history(bb_period, rsi_period, ema_period if use_ema_filter else None)
    if len(df) < needed:
        return _insufficient_history(df, needed)

    _, _, close = ensure_ohlc(df)
    mid, upper, lower = bollinger_bands(close, bb_period, bb_std)
    rsi_series = rsi(close, rsi_period)
    ema_filter = ema(close, ema_period) if use_ema_filter else None

    price = float(close.iloc[-1])
    upper_val = float(upper.iloc[-1])
    lower_val = float(lower.iloc[-1])
    rsi_val = float(rsi_series.iloc[-1])
    ema_val = float(ema_filter.iloc[-1]) if ema_filter is not None else None

    reasons = []
    long_band = price < lower_val
    short_band = price > upper_val
    rsi_long = rsi_val < rsi_os
    rsi_short = rsi_val > rsi_ob
    trend_ok_long = True
    trend_ok_short = True
    if use_ema_filter and ema_val is not None:
        trend_ok_long = price > ema_val
        trend_ok_short = price < ema_val

    reasons.append("close<bb_lower" if long_band else "close>=bb_lower")
    reasons.append("close>bb_upper" if short_band else "close<=bb_upper")
    reasons.append("rsi<rsi_os" if rsi_long else "rsi>=rsi_os")
    reasons.append("rsi>rsi_ob" if rsi_short else "rsi<=rsi_ob")
    if use_ema_filter:
        reasons.append("trend_filter_ok" if trend_ok_long or trend_ok_short else "trend_filter_block")

    if long_band and rsi_long and trend_ok_long:
        action = "BUY"
        primary_reason = "mean_reversion_long"
    elif short_band and rsi_short and trend_ok_short:
        action = "SELL"
        primary_reason = "mean_reversion_short"
    else:
        action = "HOLD"
        primary_reason = "no_signal"

    decision = {
        "action": action,
        "side": action,
        "reason": primary_reason,
        "reasons": reasons,
        "price": price,
        "rsi": rsi_val,
        "indicators": {
            "bb_upper": upper_val,
            "bb_lower": lower_val,
            "rsi": rsi_val,
            "ema_filter": ema_val,
        },
        "sl": None,
        "tp": None,
    }
    return decision


class Strategy:
    @staticmethod
    def decide(*args, **kwargs):
        return generate_signal(*args, **kwargs)


def decide(*args, **kwargs):
    return generate_signal(*args, **kwargs)


def signal(*args, **kwargs):
    return decide(*args, **kwargs)
