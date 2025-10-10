from __future__ import annotations
from typing import Optional
import pandas as pd

def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = (delta.where(delta > 0, 0.0)).rolling(period).mean()
    down = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = up / (down.replace(0, 1e-9))
    return 100.0 - (100.0 / (1.0 + rs))

def atr(df_or_high, period: int = 14, low: Optional[pd.Series] = None, close: Optional[pd.Series] = None) -> pd.Series:
    """Compatibility ATR.
    Accepts either:
      - atr(df, period) where df has 'high','low','close'
      - atr(high, period, low=..., close=...)
    """
    if isinstance(df_or_high, pd.DataFrame):
        high = df_or_high['high'] if 'high' in df_or_high else df_or_high['High']
        low_s = df_or_high['low'] if 'low' in df_or_high else df_or_high['Low']
        close_s = df_or_high['close'] if 'close' in df_or_high else df_or_high['Close']
    else:
        high = df_or_high
        low_s = low
        close_s = close
        if low_s is None or close_s is None:
            raise TypeError("atr(high, period, low=..., close=...) requires low and close")
    prev_close = close_s.shift(1)
    tr = pd.concat([high - low_s, (high - prev_close).abs(), (low_s - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


# === COMPAT START (generated) ===
# Minimal compatibility wrappers expected by tests.

import pandas as pd
import numpy as np
from typing import Optional

# EMA wrapper to accept period= as keyword
if "ema" in globals():
    _orig_ema = ema
    def ema(x, period=14, *args, **kwargs):
        return _orig_ema(x, period, *args, **kwargs)

# RSI wrapper to accept period= as keyword
if "rsi" in globals():
    _orig_rsi = rsi
    def rsi(x, period=14, *args, **kwargs):
        return _orig_rsi(x, period, *args, **kwargs)

# Flexible ATR: supports atr(df, period) and atr(high, period, low=..., close=...)
# and also atr(high, low, close, period)
def atr(*args, **kwargs):
    import pandas as pd
    # Named args route first
    if "high" in kwargs and "low" in kwargs and "close" in kwargs:
        high = kwargs["high"]; low = kwargs["low"]; close = kwargs["close"]
        period = int(kwargs.get("period", 14))
    else:
        # Positional forms
        if len(args) == 2 and hasattr(args[0], "columns"):
            df, period = args
            high = df["high"] if "high" in df else (df["High"] if "High" in df else df.iloc[:,0])
            low  = df["low"]  if "low"  in df else (df["Low"]  if "Low"  in df else df.iloc[:,0])
            close= df["close"]if "close" in df else (df["Close"]if "Close" in df else df.iloc[:,0])
        elif len(args) == 4 and hasattr(args[0], "shift"):
            # atr(high, low, close, period)
            high, low, close, period = args
            period = int(period)
        elif len(args) >= 2 and hasattr(args[0], "shift") and not hasattr(args[1], "shift"):
            # atr(high, period, low=..., close=...)
            high, period = args[:2]; period = int(period)
            low = kwargs.get("low"); close = kwargs.get("close")
            if low is None or close is None:
                raise TypeError("atr(high, period, low=..., close=...) requires low and close")
        else:
            raise TypeError("Unsupported atr signature")
    prev_close = close.shift(1).fillna(close)
    tr = pd.concat([(high-low).abs(), (high-prev_close).abs(), (low-prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(int(period), min_periods=1).mean()
# === COMPAT END ===
