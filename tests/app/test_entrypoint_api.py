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
    args = NS(
        sleep=1.5,
        enabled=True,
        paper=True,
        dry_run_only=False,
        symbol="ETHUSDT",
        strategy="ema_rsi_atr",
    )
    # isolate env
    monkeypatch.delenv("LOOP_SLEEP_SEC", raising=False)
    monkeypatch.delenv("TRADE_ENABLED", raising=False)
    monkeypatch.delenv("PAPER_TRADING", raising=False)
    monkeypatch.delenv("DRY_RUN_ONLY", raising=False)
    monkeypatch.delenv("SYMBOL", raising=False)
    monkeypatch.delenv("STRATEGY_NAME", raising=False)

    ep._apply_overrides(args)
    assert os.environ.get("LOOP_SLEEP_SEC") == "1.5"
    assert os.environ.get("TRADE_ENABLED") == "1"
    assert os.environ.get("PAPER_TRADING") == "1"
    assert os.environ.get("DRY_RUN_ONLY") == "0"
    assert os.environ.get("SYMBOL") == "ETHUSDT"
    assert os.environ.get("STRATEGY_NAME") == "ema_rsi_atr"

def test_entrypoint_env_precedence_no_cli(monkeypatch):
    ep = importlib.import_module("app.entrypoint")
    bootstrap = importlib.import_module("app.bootstrap")
    monkeypatch.setenv("PAPER_TRADING", "1")
    monkeypatch.setenv("TRADE_ENABLED", "1")
    monkeypatch.setenv("DRY_RUN_ONLY", "1")

    args = ep._parse_args([])
    ep._apply_overrides(args)
    cfg = bootstrap.resolve_runtime_mode()

    assert cfg.paper_trading is True
    assert cfg.trade_enabled is True
    assert cfg.dry_run_only is True

def test_entrypoint_cli_override(monkeypatch):
    ep = importlib.import_module("app.entrypoint")
    bootstrap = importlib.import_module("app.bootstrap")
    monkeypatch.setenv("PAPER_TRADING", "1")
    monkeypatch.setenv("TRADE_ENABLED", "1")
    monkeypatch.setenv("DRY_RUN_ONLY", "1")

    args = ep._parse_args(["--no-paper", "--disabled", "--live"])
    ep._apply_overrides(args)
    cfg = bootstrap.resolve_runtime_mode()

    assert cfg.paper_trading is False
    assert cfg.trade_enabled is False
    assert cfg.dry_run_only is False
