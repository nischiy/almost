import logging

import pandas as pd

from app.run import TraderApp


class FakeMD:
    def get_klines(self, symbol, interval, limit=1000):
        return pd.DataFrame(
            {
                "open_time": [pd.Timestamp("2025-01-01", tz="UTC")],
                "open": [100.0],
                "high": [101.0],
                "low": [99.0],
                "close": [100.0],
                "volume": [1.0],
                "close_time": [pd.Timestamp("2025-01-01", tz="UTC")],
            }
        )


class FakeSIG:
    def decide(self, df, params):
        return {"action": "HOLD", "reason": "no_signal"}


class FakeRISK:
    def can_open(self, decision):
        return True, "ok"


def test_preflight_reads_logged_on_hold(monkeypatch, caplog):
    from app.services import order_service

    monkeypatch.setenv("DRY_RUN_ONLY", "1")
    calls = {}

    def fake_preflight(symbol, wallet_usdt=None):
        calls["called"] = True
        return {
            "account": {
                "equity_usd": 1000.0,
                "wallet_usdt": 1000.0,
                "source": "exchange",
                "ts": 1700000000.0,
            },
            "filters": {
                "step_size": 0.01,
                "min_qty": 0.001,
                "min_notional": 5.0,
                "source": "exchange",
                "ts": 1700000000.0,
            },
            "price": {"value": 100.0, "source": "exchange", "ts": 1700000000.0},
            "rejects": [],
        }

    monkeypatch.setattr(order_service, "preflight_read", fake_preflight)

    app = TraderApp(cfg=None)
    app.md = FakeMD()
    app.sig = FakeSIG()
    app.risk = FakeRISK()

    class FakeEXE:
        def place(self, decision):
            calls["place"] = True

    app.exe = FakeEXE()

    caplog.set_level(logging.INFO)
    app.run_once()

    assert calls.get("called") is True
    assert calls.get("place") is None

    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "tick_summary" in log_text
    assert "equity_usd" in log_text
    assert "step_size" in log_text
    assert "min_notional" in log_text
    assert "price" in log_text
