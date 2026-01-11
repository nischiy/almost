from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


def _make_frame(limit: int = 50) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    idx = pd.date_range(end=now, periods=limit, freq="1min", tz="UTC")
    base = 100.0
    data = {
        "open_time": idx,
        "open": base,
        "high": base + 0.1,
        "low": base - 0.1,
        "close": base,
        "volume": 1.0,
        "close_time": idx,
    }
    df = pd.DataFrame(data)
    df.insert(0, "time", df["open_time"])
    return df


def get_klines(symbol: str, interval: str, limit: int = 1000, **_: Any) -> pd.DataFrame:
    return _make_frame(limit=min(limit, 50))


def get_latest_price(symbol: str, **_: Any) -> float:
    return 100.0
