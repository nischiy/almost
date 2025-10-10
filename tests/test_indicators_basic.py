
import numpy as np
import pandas as pd

from core.indicators import ema, rsi, atr

def _make_ohlc(n=200, seed=0):
    rng = np.random.default_rng(seed)
    steps = rng.normal(0, 1, size=n).cumsum() + 100
    close = pd.Series(steps, name="close")
    high = close + rng.uniform(0.1, 1.0, size=n)
    low = close - rng.uniform(0.1, 1.0, size=n)
    open_ = close.shift(1).fillna(close.iloc[0])
    vol = pd.Series(rng.uniform(1, 10, size=n), name="volume")
    df = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": vol})
    return df

def test_indicators_shapes_and_nans():
    df = _make_ohlc()
    e = ema(df["close"], 12)
    assert len(e) == len(df)
    assert np.isfinite(e.iloc[-1])
    rs = rsi(df["close"], 14)
    assert len(rs) == len(df)
    assert 0 <= rs.iloc[-1] <= 100
    a = atr(df["high"], df["low"], df["close"], 14)
    assert len(a) == len(df)
    assert a.iloc[-1] >= 0
