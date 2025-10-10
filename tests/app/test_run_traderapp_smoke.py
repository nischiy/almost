import importlib

class FakeMD:
    def get_klines(self, symbol, interval, limit=60):
        import pandas as pd, numpy as np
        idx = pd.date_range("2024-01-01", periods=10, freq="1min")
        base = 100.0 + np.linspace(0, 1, len(idx))
        return pd.DataFrame({
            "open_time": idx, "open": base, "high": base+0.3, "low": base-0.3,
            "close": base+0.1, "volume": 1.0
        })

class FakeSIG:
    def decide(self, df, params=None):
        return {"action": "LONG", "price": float(df['close'].iloc[-1]), "qty": 1.0, "reason": "test"}

class FakeRISK:
    def can_open(self, decision):
        return True, ""

class FakeEXE:
    def __init__(self): self.calls = 0
    def place(self, decision): self.calls += 1

class FakeTEL:
    def health(self, ok=True, msg="", **kw): pass
    def decision(self, data): pass
    def snapshot(self, df): pass

def test_traderapp_run_once_exec_called(monkeypatch):
    run = importlib.import_module("app.run")
    app = run.TraderApp(symbol="BTCUSDT", interval="1m")
    # attach fakes
    app.md, app.sig, app.risk, app.exe, app.tel = FakeMD(), FakeSIG(), FakeRISK(), FakeEXE(), FakeTEL()
    app.run_once()
    assert app.exe.calls == 1
