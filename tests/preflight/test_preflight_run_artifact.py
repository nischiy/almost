
import os
from pathlib import Path
import json
import time

from tools.preflight import preflight_all as PF


def test_run_writes_artifact(tmp_path, monkeypatch):
    # Run in isolated CWD so logs/ are created here
    os.chdir(tmp_path)

    # Fake environment loader
    fake_env = {
        "ENV": "dev",
        "EXCHANGE": "BINANCE",
        "SYMBOL": "BTCUSDT",
        "INTERVAL": "1m",
        "QUOTE_ASSET": "USDT",
        "ORDER_QTY_USD": "10",
        "RISK_MAX_TRADES_PER_DAY": "5",
        "PAPER_TRADING": "1",
        "TRADE_ENABLED": "0",
        "BINANCE_TESTNET": "true",
    }
    monkeypatch.setattr(PF, "load_env_file", lambda *a, **k: (fake_env, None), raising=True)

    # Make modules check green
    monkeypatch.setattr(PF, "check_modules", lambda: {"ok": True, "modules": [], "uvloop": {"ok": True}}, raising=True)

    # Skip real connectivity; mark ok
    from tools.preflight import binance_checks
    monkeypatch.setattr(binance_checks, "connectivity", lambda env, symbol: {"ok": True, "ping_ms": 42, "clock_drift_ms": 5}, raising=True)

    rc = PF.run()
    assert rc == 0

    # Verify artifact exists
    pref = Path("logs") / "preflight"
    assert pref.exists()
    # find newest json
    files = list(pref.rglob("preflight_*.json"))
    assert files, "preflight json not found"
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data.get("ok") is True
    assert "connectivity" in data and data["connectivity"].get("ok") is True
