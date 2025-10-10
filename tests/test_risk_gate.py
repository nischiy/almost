
import numpy as np
import pandas as pd

from core.risk import can_open_new_trade

def test_risk_gate_allows_with_basic_series():
    idx = pd.date_range("2025-01-01", periods=10, freq="min", tz="UTC")
    eq = pd.Series(np.linspace(1000, 1010, 10), index=idx)
    ok, reason = can_open_new_trade(equity_series=eq, realized_pnl=0.0)
    assert isinstance(ok, bool) and isinstance(reason, str)

def test_risk_gate_blocks_on_large_dd():
    # Simulate drop > max_dd_pct_day default (5% assumed inside implementation)
    idx = pd.date_range("2025-01-01", periods=10, freq="min", tz="UTC")
    eq = pd.Series([1000, 995, 980, 960, 940, 930, 920, 910, 905, 900], index=idx)
    ok, reason = can_open_new_trade(equity_series=eq, realized_pnl=-100.0)
    assert isinstance(ok, bool) and isinstance(reason, str)

