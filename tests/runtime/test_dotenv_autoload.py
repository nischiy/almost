# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import os
from pathlib import Path


def test_dotenv_autoload_from_repo_root(monkeypatch) -> None:
    root = Path(__file__).resolve().parents[2]
    env_path = root / ".env"
    original = env_path.read_text(encoding="utf-8") if env_path.exists() else None

    payload = "\n".join(
        [
            "PAPER_TRADING=1",
            "TRADE_ENABLED=1",
            "DRY_RUN_ONLY=1",
            "SYMBOL=ETHUSDT",
            "INTERVAL=5m",
            "STRATEGY_NAME=test_strategy",
            "BINANCE_TESTNET=1",
            "API_KEY=dummy",
            "API_SECRET=dummy",
        ]
    )

    try:
        env_path.write_text(payload, encoding="utf-8")
        for key in [
            "PAPER_TRADING",
            "TRADE_ENABLED",
            "DRY_RUN_ONLY",
            "SYMBOL",
            "INTERVAL",
            "STRATEGY_NAME",
            "BINANCE_TESTNET",
            "API_KEY",
            "API_SECRET",
        ]:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.delenv("DOTENV_DISABLE", raising=False)

        env_mod = importlib.import_module("core.config.env")
        importlib.reload(env_mod)

        assert env_mod.load_dotenv_once() is True
        assert os.environ.get("SYMBOL") == "ETHUSDT"
        assert env_mod.get_bool("PAPER_TRADING", False) is True
        assert env_mod.get_bool("TRADE_ENABLED", False) is True
        assert env_mod.get_bool("DRY_RUN_ONLY", False) is True
        assert env_mod.get_bool("BINANCE_TESTNET", False) is True
    finally:
        if original is None:
            if env_path.exists():
                env_path.unlink()
        else:
            env_path.write_text(original, encoding="utf-8")
