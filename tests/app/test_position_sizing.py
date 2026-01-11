# -*- coding: utf-8 -*-
"""
Tests for deterministic USD sizing and rounding in order_adapter/order_service.
"""
from __future__ import annotations

import importlib
import os


def _place(symbol: str, **kwargs):
    os.environ["DRY_RUN_ONLY"] = "1"
    svc = importlib.import_module("app.services.order_service")
    res = svc.place(symbol, "BUY", "MARKET", kwargs.pop("wallet_usdt", 1000), **kwargs)
    return res.get("preview", {})


def test_sizing_uses_equity_risk(monkeypatch):
    monkeypatch.setenv("ORDER_QTY_USD", "50")
    monkeypatch.setenv("RISK_PER_TRADE_PCT", "0.5")
    monkeypatch.setenv("RISK_MAX_POS_USD", "100")
    monkeypatch.setenv("OFFLINE_PRICE", "200")
    monkeypatch.setenv("OFFLINE_STEP_SIZE", "0.01")
    monkeypatch.setenv("OFFLINE_MIN_QTY", "0.001")
    monkeypatch.setenv("OFFLINE_MIN_NOTIONAL", "0")

    preview = _place("BTCUSDT", rg_state={"equity_usd": 10000})
    sizer = preview["sizer"]

    assert sizer["size_usd"] == 50.0
    assert sizer["qty_raw"] == 0.25
    assert sizer["qty_final"] == 0.25
    assert sizer["qty"] == 0.25


def test_sizing_fallback_without_equity(monkeypatch):
    monkeypatch.setenv("ORDER_QTY_USD", "40")
    monkeypatch.setenv("RISK_PER_TRADE_PCT", "1")
    monkeypatch.setenv("OFFLINE_PRICE", "100")
    monkeypatch.setenv("OFFLINE_STEP_SIZE", "0.01")
    monkeypatch.setenv("OFFLINE_MIN_QTY", "0.001")
    monkeypatch.setenv("OFFLINE_MIN_NOTIONAL", "0")

    preview = _place("BTCUSDT", wallet_usdt=0)
    sizer = preview["sizer"]

    assert sizer["size_usd"] == 40.0
    assert sizer["qty_raw"] == 0.4
    assert sizer["qty_final"] == 0.4


def test_rounding_floor_and_min_qty_block(monkeypatch):
    monkeypatch.setenv("ORDER_QTY_USD", "1")
    monkeypatch.setenv("OFFLINE_PRICE", "100")
    monkeypatch.setenv("OFFLINE_STEP_SIZE", "0.1")
    monkeypatch.setenv("OFFLINE_MIN_QTY", "0.05")
    monkeypatch.setenv("OFFLINE_MIN_NOTIONAL", "0")

    preview = _place("BTCUSDT", wallet_usdt=0)
    assert preview.get("order_payload") is None
    blockers = preview.get("blockers") or []
    assert any("qty_below_min_qty" in b for b in blockers)


def test_rounding_floor_to_step(monkeypatch):
    monkeypatch.setenv("ORDER_QTY_USD", "123")
    monkeypatch.setenv("OFFLINE_PRICE", "100")
    monkeypatch.setenv("OFFLINE_STEP_SIZE", "0.1")
    monkeypatch.setenv("OFFLINE_MIN_QTY", "0.001")
    monkeypatch.setenv("OFFLINE_MIN_NOTIONAL", "0")

    preview = _place("BTCUSDT", wallet_usdt=0)
    sizer = preview["sizer"]

    assert sizer["qty_raw"] == 1.23
    assert sizer["qty_final"] == 1.2
    assert sizer["qty"] == 1.2
