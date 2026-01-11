from __future__ import annotations

from typing import Iterable, Tuple

import pandas as pd


def _pick_col(df: pd.DataFrame, *cands: str) -> pd.Series | None:
    for name in cands:
        if name in df:
            return df[name]
    lower = {str(c).lower(): c for c in getattr(df, "columns", [])}
    for name in cands:
        key = str(name).lower()
        if key in lower:
            return df[lower[key]]
    return None


def ensure_ohlc(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
    close = _pick_col(df, "close", "Close", "c", "C", "price", "Price", "last", "Last")
    if close is None:
        raise KeyError("close/Close not found in DataFrame columns")
    high = _pick_col(df, "high", "High", "h", "H", "HighPrice", "max", "Max")
    low = _pick_col(df, "low", "Low", "l", "L", "LowPrice", "min", "Min")
    if high is None:
        high = close
    if low is None:
        low = close
    return high, low, close


def ensure_volume(df: pd.DataFrame) -> pd.Series | None:
    return _pick_col(df, "volume", "Volume", "v", "V")


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=int(span), adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(int(period), min_periods=int(period)).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.where(delta > 0, 0.0).rolling(int(period), min_periods=int(period)).mean()
    down = (-delta.where(delta < 0, 0.0)).rolling(int(period), min_periods=int(period)).mean()
    rs = up / (down.replace(0, 1e-9))
    return 100.0 - (100.0 / (1.0 + rs))


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = ensure_ohlc(df)
    prev_close = close.shift(1).fillna(close)
    tr_components = [
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ]
    tr = pd.concat(tr_components, axis=1).max(axis=1)
    return tr.rolling(int(period), min_periods=int(period)).mean()


def bollinger_bands(close: pd.Series, period: int = 20, std_mult: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    mid = close.rolling(int(period), min_periods=int(period)).mean()
    std = close.rolling(int(period), min_periods=int(period)).std()
    upper = mid + float(std_mult) * std
    lower = mid - float(std_mult) * std
    return mid, upper, lower


def donchian_channel(df: pd.DataFrame, period: int = 20) -> Tuple[pd.Series, pd.Series]:
    high, low, _ = ensure_ohlc(df)
    high_band = high.rolling(int(period), min_periods=int(period)).max()
    low_band = low.rolling(int(period), min_periods=int(period)).min()
    return high_band, low_band


def required_history(*lengths: Iterable[int | float | None]) -> int:
    values = [int(x) for x in lengths if x is not None]
    return max(values) if values else 1
