
import os
import types
import builtins
import importlib
import pathlib
import json

import pytest

from tools.preflight import preflight_all as PF


def test_validate_env_minimal_live_ok(tmp_path, monkeypatch):
    env = {
        "ENV": "prod",
        "EXCHANGE": "BINANCE",
        "SYMBOL": "BTCUSDT",
        "INTERVAL": "1m",
        "QUOTE_ASSET": "USDT",
        "ORDER_QTY_USD": "50",
        "RISK_MAX_TRADES_PER_DAY": "15",
        "PAPER_TRADING": "0",
        "TRADE_ENABLED": "1",
        "BINANCE_TESTNET": "false",
        "BINANCE_API_KEY": "x",
        "BINANCE_API_SECRET": "y",
        "RISK_MAX_LOSS_USD_DAY": "100",
        "RISK_MAX_DD_PCT_DAY": "5",
        "RISK_MAX_POS_USD": "1000",
        "RISK_MIN_EQUITY_USD": "50",
    }
    res = PF.validate_env(env)
    assert res["ok"] is True
    assert res["creds_ok"] is True
    assert res["flags"]["BINANCE_TESTNET"] is False
    # sanity values parsed to float and positive
    assert res["risk"]["RISK_MAX_LOSS_USD_DAY"] == 100.0
    assert res["risk"]["RISK_MAX_DD_PCT_DAY"] == 5.0


def test_validate_env_paper_no_creds_ok(monkeypatch):
    env = {
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
    res = PF.validate_env(env)
    assert res["ok"] is True
    assert res["creds_ok"] is True  # not required in paper
