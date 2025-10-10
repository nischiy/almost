# core/indicators.py
# Release-grade, dependency-light (numpy+pandas) technical indicators.
# Safe for production: numeric coercion, NaN-tolerant, and typed.
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Optional, Sequence, Dict
import numpy as np
import pandas as pd

__all__ = [
    "sma", "ema", "wma", "rma",
    "rsi", "atr", "tr", "macd",
    "stoch_kd", "bbands", "adx", "dmi",
    "vwap", "roc", "obv", "supertrend",
    "normalize_numeric",
]

_NP_FLOAT = np.float64

# ---------- helpers ----------

def normalize_numeric(s: pd.Series) -> pd.Series:
    """Coerce to float Series, keep index, preserve NaNs; fill inf with NaN."""
    s = pd.to_numeric(s, errors="coerce")
    s = s.astype(_NP_FLOAT, copy=False)
    s = s.replace([np.inf, -np.inf], np.nan)
    return s

def _span_or_alpha(period: int) -> Tuple[int, float]:
    p = max(1, int(period))
    alpha = 1.0 / p
    return p, alpha

# ---------- moving averages ----------

def sma(s: pd.Series, period: int) -> pd.Series:
    s = normalize_numeric(s)
    p = max(1, int(period))
    return s.rolling(window=p, min_periods=1).mean()

def ema(s: pd.Series, period: int, adjust: bool = False) -> pd.Series:
    s = normalize_numeric(s)
    p, _ = _span_or_alpha(period)
    return s.ewm(span=p, adjust=adjust).mean()

def wma(s: pd.Series, period: int) -> pd.Series:
    """Linear weighted moving average."""
    s = normalize_numeric(s)
    p = max(1, int(period))
    weights = np.arange(1, p + 1, dtype=_NP_FLOAT)
    def _calc(x: np.ndarray) -> _NP_FLOAT:
        # x has length <= p due to min_periods=1
        w = weights[-len(x):]
        return (x * w).sum() / w.sum()
    return s.rolling(window=p, min_periods=1).apply(_calc, raw=True)

def rma(s: pd.Series, period: int) -> pd.Series:
    """Wilder's RMA (aka SMMA)."""
    s = normalize_numeric(s)
    p, alpha = _span_or_alpha(period)
    # RMA equivalent: ewm(alpha=1/p, adjust=False)
    return s.ewm(alpha=alpha, adjust=False).mean()

# ---------- momentum / volatility ----------

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder RSI."""
    c = normalize_numeric(close)
    delta = c.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    rs_up = rma(up, period)
    rs_down = rma(down, period)
    rs = rs_up / rs_down.replace(0.0, np.nan)
    r = 100.0 - (100.0 / (1.0 + rs))
    # Seed neutral 50 where insufficient history
    return r.fillna(50.0)

def tr(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """True Range (vectorized)."""
    h = normalize_numeric(high)
    l = normalize_numeric(low)
    c = normalize_numeric(close)
    pc = c.shift(1)
    tr1 = h - l
    tr2 = (h - pc).abs()
    tr3 = (l - pc).abs()
    out = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return out

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range (Wilder)."""
    return rma(tr(high, low, close), period)

def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    c = normalize_numeric(close)
    macd_line = ema(c, fast) - ema(c, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist}, index=c.index)

def stoch_kd(high: pd.Series, low: pd.Series, close: pd.Series, k: int = 14, d: int = 3) -> pd.DataFrame:
    h = normalize_numeric(high)
    l = normalize_numeric(low)
    c = normalize_numeric(close)
    hh = h.rolling(window=max(1,k), min_periods=1).max()
    ll = l.rolling(window=max(1,k), min_periods=1).min()
    denom = (hh - ll).replace(0.0, np.nan)
    k_line = 100.0 * (c - ll) / denom
    d_line = sma(k_line, d)
    return pd.DataFrame({"%K": k_line, "%D": d_line}, index=c.index)

def bbands(close: pd.Series, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    c = normalize_numeric(close)
    m = sma(c, period)
    std = c.rolling(window=max(1,period), min_periods=1).std(ddof=0)
    upper = m + num_std * std
    lower = m - num_std * std
    width = (upper - lower) / m.replace(0.0, np.nan)
    return pd.DataFrame({"mid": m, "upper": upper, "lower": lower, "width": width}, index=c.index)

def dmi(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.DataFrame:
    """Directional Movement Index (DI+, DI-)."""
    h = normalize_numeric(high)
    l = normalize_numeric(low)
    c = normalize_numeric(close)
    up_move = h.diff()
    down_move = -l.diff()
    plus_dm = ((up_move > down_move) & (up_move > 0)).astype(_NP_FLOAT) * up_move.clip(lower=0.0)
    minus_dm = ((down_move > up_move) & (down_move > 0)).astype(_NP_FLOAT) * down_move.clip(lower=0.0)
    tr_series = tr(h, l, c)
    atr_series = rma(tr_series, period)
    plus_di = 100.0 * rma(plus_dm, period) / atr_series.replace(0.0, np.nan)
    minus_di = 100.0 * rma(minus_dm, period) / atr_series.replace(0.0, np.nan)
    return pd.DataFrame({"+DI": plus_di, "-DI": minus_di}, index=c.index)

def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    dm = dmi(high, low, close, period)
    plus_di, minus_di = dm["+DI"], dm["-DI"]
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    return rma(dx, period)

def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    h = normalize_numeric(high); l = normalize_numeric(low); c = normalize_numeric(close)
    v = normalize_numeric(volume).fillna(0.0)
    tp = (h + l + c) / 3.0
    cum_pv = (tp * v).cumsum()
    cum_v = v.cumsum().replace(0.0, np.nan)
    return cum_pv / cum_v

def roc(series: pd.Series, period: int = 1) -> pd.Series:
    s = normalize_numeric(series)
    p = max(1, int(period))
    return 100.0 * (s / s.shift(p) - 1.0)

def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    c = normalize_numeric(close)
    v = normalize_numeric(volume).fillna(0.0)
    sign = np.sign(c.diff().fillna(0.0))
    return (v * sign).cumsum()

# ---------- supertrend (popular ATR-based trailing) ----------

@dataclass
class SupertrendResult:
    supertrend: pd.Series
    direction: pd.Series  # +1 uptrend, -1 downtrend

def supertrend(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 10, multiplier: float = 3.0) -> SupertrendResult:
    """Vectorized-ish supertrend. Returns line and direction (+1/-1)."""
    h = normalize_numeric(high)
    l = normalize_numeric(low)
    c = normalize_numeric(close)

    atr_val = atr(h, l, c, period)
    hl2 = (h + l) / 2.0
    upperband = hl2 + multiplier * atr_val
    lowerband = hl2 - multiplier * atr_val

    st = pd.Series(index=c.index, dtype=_NP_FLOAT)
    dirn = pd.Series(index=c.index, dtype=_NP_FLOAT)

    prev_st = np.nan
    prev_dir = 1.0  # start with uptrend by default

    for i in range(len(c)):
        ub = upperband.iat[i]
        lb = lowerband.iat[i]
        price = c.iat[i]

        # persist bands
        if i > 0:
            ub = min(ub, upperband.iat[i-1]) if prev_dir > 0 else ub
            lb = max(lb, lowerband.iat[i-1]) if prev_dir < 0 else lb

        # direction switch
        curr_dir = prev_dir
        if prev_st is np.nan or np.isnan(prev_st):
            curr_dir = 1.0
        else:
            if price > prev_st:
                curr_dir = 1.0
            elif price < prev_st:
                curr_dir = -1.0

        curr_st = lb if curr_dir > 0 else ub

        st.iat[i] = curr_st
        dirn.iat[i] = curr_dir
        prev_st, prev_dir = curr_st, curr_dir

    # Ensure nice dtypes
    dirn = dirn.fillna(method="ffill").fillna(1.0)
    st = st.astype(_NP_FLOAT)
    dirn = dirn.astype(_NP_FLOAT)
    return SupertrendResult(supertrend=st, direction=dirn)
