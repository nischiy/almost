# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib


def test_order_service_dry_run_builds_payload_with_wallet_equity(monkeypatch) -> None:
    monkeypatch.setenv("DRY_RUN_ONLY", "1")
    monkeypatch.setenv("RISK_MIN_EQUITY_USD", "10")

    svc = importlib.import_module("app.services.order_service")
    res = svc.place("BTCUSDT", "BUY", "MARKET", 1000.0, rg_state={})

    assert res["reason"] == "dry_run"
    preview = res["preview"]
    assert isinstance(preview.get("order_payload"), dict)

    gate = preview.get("risk_gate", {})
    assert gate.get("can_trade") is True
    violations = (gate.get("reason") or {}).get("violations", [])
    assert not any(v.get("limit") == "min_equity_usd" for v in violations)
