import pandas as pd

def test_traderapp_run_once_exec_called(monkeypatch, df_klines):
    from app.run import TraderApp

    app = TraderApp(cfg=None)

    # stub md
    class MD:
        def get_klines(self, symbol, interval, limit=1000):
            return df_klines
    app.md = MD()

    # stub signal
    class SIG:
        def decide(self, df, params):
            return {"action":"LONG","price":float(df['close'].iloc[-1]),"qty":0.001}
    app.sig = SIG()

    # stub risk
    class RISK:
        def can_open(self, decision):
            return True, ""
    app.risk = RISK()

    # capture execution
    calls = {}
    class EXE:
        def place(self, decision):
            calls["decision"] = decision
    app.exe = EXE()

    # stub telemetry (no-ops)
    class TEL:
        def snapshot(self, df): pass
        def decision(self, d): pass
        def health(self, ok=True, msg="", **kw): pass
    app.tel = TEL()

    app.run_once()
    assert "decision" in calls
    assert calls["decision"]["action"] in {"LONG","SHORT"}
