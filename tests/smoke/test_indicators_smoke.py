# smoke: a couple simple indicator calls
import pandas as pd
import numpy as np
import core.indicators as I

def test_indicators_rsi_ema():
    s = pd.Series(np.linspace(1, 100, 100))
    rsi = I.rsi(s, period=14)
    ema = I.ema(s, period=20)
    assert rsi.notna().sum() > 0
    assert ema.notna().sum() > 0
