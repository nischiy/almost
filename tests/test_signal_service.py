
import pandas as pd
from app.services.signal import SignalService

def make_df(n=100, base=100.0):
    import numpy as np
    idx = pd.date_range("2025-01-01", periods=n, freq="1min", tz="UTC")
    close = base + np.cumsum(np.random.randn(n)*0.1)
    high = close + 0.2
    low = close - 0.2
    return pd.DataFrame({"open_time": idx, "open": close, "high": high, "low": low, "close": close, "volume": 1.0, "close_time": idx})

def test_signal_decide_runs():
    df = make_df()
    sig = SignalService()
    params = {"ema_fast": 5, "ema_slow": 10, "rsi_len": 14, "rsi_buy": 55, "rsi_sell": 45, "atr_len": 14, "sl_atr_mult": 2.0, "tp_r_mult": 1.5}
    dec = sig.decide(df, params)
    assert "side" in dec and "reason" in dec and "sl" in dec and "tp" in dec
