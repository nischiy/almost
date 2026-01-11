import pandas as pd

from core.logic import breakout_donchian_atr, mean_reversion_bb_rsi, trend_pullback_ema_atr
from core.logic.indicators import atr, ema


def _make_df(prices, volume=100.0):
    data = {
        "open": prices,
        "high": prices,
        "low": prices,
        "close": prices,
        "volume": [volume] * len(prices),
    }
    return pd.DataFrame(data)


def _make_trend_df(length, start, step):
    prices = [start + step * i for i in range(length)]
    data = {
        "open": prices,
        "high": [p + 0.5 for p in prices],
        "low": [p - 0.5 for p in prices],
        "close": prices,
        "volume": [100.0] * length,
    }
    return pd.DataFrame(data)


def test_breakout_donchian_atr_buy():
    prices = [100.0 + i * 0.2 for i in range(24)] + [110.0]
    df = _make_df(prices, volume=100.0)
    df.loc[df.index[-1], "volume"] = 200.0
    out = breakout_donchian_atr.decide(df, params={"use_ema200_filter": False, "volume_ratio_threshold": 1.2})
    assert out["action"] == "BUY"


def test_breakout_donchian_atr_sell():
    prices = [120.0 - i * 0.2 for i in range(24)] + [100.0]
    df = _make_df(prices, volume=100.0)
    df.loc[df.index[-1], "volume"] = 200.0
    out = breakout_donchian_atr.decide(df, params={"use_ema200_filter": False, "volume_ratio_threshold": 1.2})
    assert out["action"] == "SELL"


def test_breakout_donchian_atr_insufficient_history():
    df = _make_df([100.0 + i for i in range(10)])
    out = breakout_donchian_atr.decide(df, params={})
    assert out["action"] == "HOLD"
    assert out["reason"] == "insufficient_history"


def test_mean_reversion_bb_rsi_buy():
    prices = [100.0] * 24 + [90.0]
    df = _make_df(prices)
    out = mean_reversion_bb_rsi.decide(df, params={"use_ema200_filter": False})
    assert out["action"] == "BUY"


def test_mean_reversion_bb_rsi_sell():
    prices = [100.0] * 24 + [110.0]
    df = _make_df(prices)
    out = mean_reversion_bb_rsi.decide(df, params={"use_ema200_filter": False})
    assert out["action"] == "SELL"


def test_mean_reversion_bb_rsi_insufficient_history():
    df = _make_df([100.0 + i for i in range(10)])
    out = mean_reversion_bb_rsi.decide(df, params={})
    assert out["action"] == "HOLD"
    assert out["reason"] == "insufficient_history"


def test_trend_pullback_ema_atr_buy():
    df = _make_trend_df(220, 100.0, 0.2)
    close = df["close"]
    ema_fast = ema(close, 50).iloc[-1]
    atr_val = atr(df, 14).iloc[-1]
    df.loc[df.index[-1], "low"] = ema_fast - 0.5 * atr_val
    df.loc[df.index[-1], "high"] = ema_fast + 0.6 * atr_val
    df.loc[df.index[-1], "close"] = ema_fast + 0.2 * atr_val
    out = trend_pullback_ema_atr.decide(df, params={})
    assert out["action"] == "BUY"


def test_trend_pullback_ema_atr_sell():
    df = _make_trend_df(220, 200.0, -0.2)
    close = df["close"]
    ema_fast = ema(close, 50).iloc[-1]
    atr_val = atr(df, 14).iloc[-1]
    df.loc[df.index[-1], "high"] = ema_fast + 0.5 * atr_val
    df.loc[df.index[-1], "low"] = ema_fast - 0.6 * atr_val
    df.loc[df.index[-1], "close"] = ema_fast - 0.2 * atr_val
    out = trend_pullback_ema_atr.decide(df, params={})
    assert out["action"] == "SELL"


def test_trend_pullback_ema_atr_insufficient_history():
    df = _make_trend_df(50, 100.0, 0.2)
    out = trend_pullback_ema_atr.decide(df, params={})
    assert out["action"] == "HOLD"
    assert out["reason"] == "insufficient_history"
