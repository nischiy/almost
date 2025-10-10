
from __future__ import annotations
import time

def connectivity(env: dict, symbol: str) -> dict:
    """
    Lightweight connectivity check stub:
    - Pretends ping and clock-drift are fine.
    Project can override with real UMFutures logic; tests monkeypatch this anyway.
    """
    # This function is intentionally minimal as tests will monkeypatch it.
    return {"ok": True, "ping_ms": 25, "clock_drift_ms": 3, "symbol": symbol}
