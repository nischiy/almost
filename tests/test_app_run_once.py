
import pandas as pd
from app.run import TraderApp
from core.config import load_config

class FakeMD:
    def get_klines(self, symbol, interval, limit=1000):
        idx = pd.date_range("2025-01-01", periods=50, freq="1min", tz="UTC")
        df = pd.DataFrame({
            "open_time": idx, "open": 100.0, "high": 100.1, "low": 99.9, "close": 100.0, "volume": 1.0, "close_time": idx
        })
        return df

class FakeSIG:
    def decide(self, df, params):
        return {"time": df.iloc[-1]["open_time"], "side":"FLAT","reason":"test","rsi":50.0,"ema_fast":1,"ema_slow":2,"atr":0.1,"price":100.0,"sl":0.0,"tp":0.0}

class FakeRISK:
    def can_open(self, decision):
        return True, "ok"

class FakeEXE:
    def place(self, decision): pass

class FakeTEL:
    def snapshot(self, df): pass
    def decision(self, decision): pass
    def health(self, **payload): pass

def test_traderapp_run_once_with_fakes(monkeypatch):
    cfg = load_config()
    app = TraderApp(cfg)
    # inject fakes
    app.md, app.sig, app.risk, app.exe, app.tel = FakeMD(), FakeSIG(), FakeRISK(), FakeEXE(), FakeTEL()
    app.run_once()  # should not raise
