import logging

import pandas as pd

from app.run import TraderApp
from core.config import load_config


class FakeMD:
    def get_klines(self, symbol, interval, limit=1000):
        df = pd.DataFrame(
            {
                "open_time": [pd.Timestamp("2025-01-01", tz="UTC")],
                "open": [100.0],
                "high": [100.0],
                "low": [99.0],
                "close": [100.0],
                "volume": [1.0],
                "close_time": [pd.Timestamp("2025-01-01", tz="UTC")],
            }
        )
        return df


class FakeSIG:
    def decide(self, df, params):
        return {
            "action": "BUY",
            "reason": "test_reason",
            "reasons": ["ema_fast>ema_slow", "rsi>rsi_sell"],
            "price": 100.0,
            "ema_fast": 1.0,
            "ema_slow": 2.0,
            "rsi": 55.0,
            "atr": 0.5,
            "sl": 99.0,
            "tp": 102.0,
            "qty": 0.1,
            "size_usd": 10.0,
        }


class FakeRISK:
    def can_open(self, decision):
        return True, "ok"


class FakeEXE:
    def place(self, decision):
        return {
            "submitted": False,
            "reason": "dry_run",
            "preview": {
                "sizer": {
                    "size_usd": 10.0,
                    "qty_raw": 0.1,
                    "qty_final": 0.1,
                    "lot_step": 0.01,
                    "min_qty": 0.001,
                    "min_notional": 0.0,
                },
                "blockers": [],
            },
        }


class FakeTEL:
    def snapshot(self, df):
        pass

    def decision(self, decision):
        pass

    def health(self, **payload):
        pass


def test_decision_logging_includes_strategy_and_reason(monkeypatch, caplog):
    monkeypatch.setenv("STRATEGY_NAME", "test_strategy")
    cfg = load_config()
    app = TraderApp(cfg)
    app.md, app.sig, app.risk, app.exe, app.tel = FakeMD(), FakeSIG(), FakeRISK(), FakeEXE(), FakeTEL()

    caplog.set_level(logging.INFO)
    app.run_once()

    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "decision: strategy=test_strategy" in log_text
    assert "reason=test_reason" in log_text
    assert "reasons=['ema_fast>ema_slow', 'rsi>rsi_sell']" in log_text
