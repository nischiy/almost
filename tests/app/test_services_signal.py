import importlib
import pandas as pd

def test_signal_service_decide_shape(df_klines):
    mod = importlib.import_module("app.services.signal")
    sig = mod.SignalService()
    out = sig.decide(df_klines, params={"name":"ema_rsi_atr"})
    assert isinstance(out, dict)
    assert "side" in out and "reason" in out
    assert out.get("side") in {"LONG","SHORT","HOLD"}
