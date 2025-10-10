import os
import types
import importlib

def test_entrypoint_exports():
    ep = importlib.import_module("app.entrypoint")
    assert hasattr(ep, "main")
    assert hasattr(ep, "_apply_overrides")
    assert hasattr(ep, "_parse_args")

def test_apply_overrides_sets_env(monkeypatch):
    ep = importlib.import_module("app.entrypoint")
    # build a dummy Namespace
    class NS(types.SimpleNamespace): pass
    args = NS(sleep=1.5, enabled=True, paper=True, symbol="ETHUSDT", strategy="ema_rsi_atr")
    # isolate env
    monkeypatch.delenv("LOOP_SLEEP_SEC", raising=False)
    monkeypatch.delenv("TRADE_ENABLED", raising=False)
    monkeypatch.delenv("PAPER_TRADING", raising=False)
    monkeypatch.delenv("SYMBOL", raising=False)
    monkeypatch.delenv("STRATEGY_NAME", raising=False)

    ep._apply_overrides(args)
    assert os.environ.get("LOOP_SLEEP_SEC") == "1.5"
    assert os.environ.get("TRADE_ENABLED") == "1"
    assert os.environ.get("PAPER_TRADING") == "1"
    assert os.environ.get("SYMBOL") == "ETHUSDT"
    assert os.environ.get("STRATEGY_NAME") == "ema_rsi_atr"
