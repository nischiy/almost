import pandas as pd

def test_signal_decision_contains_required_keys(df_klines):
    from app.services.signal import SignalService
    s = SignalService()
    decision = s.decide(df_klines, {
        "ema_fast": 2, "ema_slow": 3, "rsi_period": 3,
        "rsi_buy": 50, "rsi_sell": 50, "atr_period": 3,
        "sl_atr": 1.0, "tp_atr": 1.5, "qty": 0.001
    })
    assert isinstance(decision, dict)
    assert "action" in decision
    assert decision["action"] in {"LONG","SHORT","HOLD"}
    # SL/TP may be present for LONG/SHORT; if hold, may be absent
    assert "price" in decision and isinstance(decision["price"], float)
