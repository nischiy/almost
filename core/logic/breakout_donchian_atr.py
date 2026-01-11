from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from core.logic.indicators import (
    atr,
    donchian_channel,
    ema,
    ensure_ohlc,
    ensure_volume,
    required_history,
    sma,
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

    donchian_period = int(params.get("donchian_period", 20))
    atr_period = int(params.get("atr_period", 14))
    vol_sma_period = int(params.get("volume_sma_period", 20))
    vol_ratio_threshold = float(params.get("volume_ratio_threshold", 1.5))
    use_ema_filter = bool(params.get("use_ema200_filter", False))
    ema_period = int(params.get("ema_filter_period", 200))
    sl_k = float(params.get("sl_atr", 1.5))
    tp_k = float(params.get("tp_atr", 2.0))

    needed = required_history(donchian_period, atr_period, vol_sma_period, ema_period if use_ema_filter else None)
    if len(df) < needed:
        return _insufficient_history(df, needed)

    high_band, low_band = donchian_channel(df, donchian_period)
    atr_series = atr(df, atr_period)
    _, _, close = ensure_ohlc(df)
    volume = ensure_volume(df)
    if volume is None:
        return {
            "action": "HOLD",
            "side": "HOLD",
            "reason": "missing_volume",
            "reasons": ["missing_volume"],
            "price": float(close.iloc[-1]),
            "indicators": {},
            "sl": None,
            "tp": None,
        }

    volume_sma = sma(volume, vol_sma_period)
    volume_ratio = float(volume.iloc[-1] / volume_sma.iloc[-1]) if volume_sma.iloc[-1] else 0.0
    ema_filter = ema(close, ema_period) if use_ema_filter else None

    price = float(close.iloc[-1])
    donchian_high = float(high_band.shift(1).iloc[-1])
    donchian_low = float(low_band.shift(1).iloc[-1])
    atr_val = float(atr_series.iloc[-1]) if not atr_series.empty else None
    ema_val = float(ema_filter.iloc[-1]) if ema_filter is not None else None

    reasons = []
    long_breakout = price > donchian_high
    short_breakout = price < donchian_low
    vol_ok = volume_ratio >= vol_ratio_threshold
    trend_ok_long = True
    trend_ok_short = True
    if use_ema_filter and ema_val is not None:
        trend_ok_long = price > ema_val
        trend_ok_short = price < ema_val

    reasons.append("breakout_up" if long_breakout else "no_breakout_up")
    reasons.append("breakout_down" if short_breakout else "no_breakout_down")
    reasons.append("vol_ok" if vol_ok else "vol_low")
    if use_ema_filter:
        reasons.append("trend_filter_ok" if trend_ok_long or trend_ok_short else "trend_filter_block")

    if long_breakout and vol_ok and trend_ok_long:
        action = "BUY"
        primary_reason = "breakout_long"
    elif short_breakout and vol_ok and trend_ok_short:
        action = "SELL"
        primary_reason = "breakout_short"
    else:
        action = "HOLD"
        primary_reason = "no_signal"

    decision: Dict[str, Any] = {
        "action": action,
        "side": action,
        "reason": primary_reason,
        "reasons": reasons,
        "price": price,
        "atr": atr_val,
        "indicators": {
            "donchian_high": donchian_high,
            "donchian_low": donchian_low,
            "volume_ratio": volume_ratio,
            "ema_filter": ema_val,
            "atr": atr_val,
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
