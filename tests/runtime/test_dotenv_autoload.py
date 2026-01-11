# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import os
from pathlib import Path


def test_dotenv_skipped_under_pytest(monkeypatch) -> None:
    root = Path(__file__).resolve().parents[2]
    env_path = root / ".env"
    original = env_path.read_text(encoding="utf-8") if env_path.exists() else None

    payload = "\n".join(
        [
            "RISK_MAX_POS_USD=100",
        ]
    )

    try:
        env_path.write_text(payload, encoding="utf-8")
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")
        monkeypatch.setenv("RISK_MAX_POS_USD", "1")
        monkeypatch.delenv("DOTENV_DISABLE", raising=False)

        env_mod = importlib.import_module("core.config.env")
        importlib.reload(env_mod)

        assert env_mod.load_dotenv_once() is False
        assert os.environ.get("RISK_MAX_POS_USD") == "1"
    finally:
        if original is None:
            if env_path.exists():
                env_path.unlink()
        else:
            env_path.write_text(original, encoding="utf-8")
