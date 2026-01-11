import pandas as pd

from app.bootstrap import compose_trader_app, resolve_runtime_mode


class FakeSignal:
    def __init__(self) -> None:
        self.called = False

    def decide(self, df: pd.DataFrame, params: dict) -> dict:
        self.called = True
        return {"side": "HOLD", "reason": "smoke"}


class FakeExe:
    def __init__(self) -> None:
        self.called = False

    def place(self, *args, **kwargs):
        self.called = True
        raise AssertionError("Execution should not be called for HOLD decisions")


def test_offline_pipeline_smoke(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_MODULE", "app.services.market_data_stub")
    cfg = resolve_runtime_mode()
    app = compose_trader_app(cfg)

    sig = FakeSignal()
    exe = FakeExe()
    app.sig = sig
    app.exe = exe

    app.run_once()

    assert sig.called is True
    assert exe.called is False
