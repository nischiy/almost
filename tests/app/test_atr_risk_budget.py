# -*- coding: utf-8 -*-
"""
Тести ATR-Risk Budget sizing у order_adapter/order_service.

Покриває:
- applied=True коли CAP дозволяє зібрати мін-лот;
- applied=False коли CAP < біржового мінімуму;
- applied=False на поганих інпутах (atr<=0/None);
- qty ніколи не перевищує CAP (після округлень);
- kill-switch блокує торгівлю незалежно від ATR-блоку.

Запуск:
    PYTHONPATH=. pytest -q tests/app/test_atr_risk_budget.py
"""

from __future__ import annotations
import os
import importlib
import json

def _place(symbol: str, **kwargs):
    """Виклик app.services.order_service.place(...) з DRY_RUN_ONLY=1 і повернення прев’ю."""
    os.environ["DRY_RUN_ONLY"] = "1"
    svc = importlib.import_module("app.services.order_service")
    res = svc.place(symbol, "BUY", "MARKET", 100, **kwargs)
    return res.get("preview", {})

def test_atr_budget_applied_true_when_cap_allows(monkeypatch):
    """
    Коли CAP достатній (наприклад, 200$ на BTCUSDT), маємо applied=True
    і qty не перевищує кришку після округлень.
    """
    monkeypatch.setenv("RISK_MAX_POS_USD", "200")
    prev = _place(
        "BTCUSDT",
        ps_mode="atr_budget",
        atr=100.0,
        tick_value=1.0,
        risk_budget_day_remaining=25.0,
        dd_pct_day=2.0,
    )
    sizer = prev["sizer"]
    meta = sizer.get("atr_budget")
    assert meta is not None, "Очікуємо наявність метаданих ATR-бюджету"
    assert meta["applied"] is True, f"Очікуємо applied=True, маємо: {json.dumps(meta, ensure_ascii=False)}"

    qty = float(sizer["qty"])
    qty_cap_floor = float(meta["qty_cap_floor"])
    lot_step = float(sizer["lot_step"])
    min_qty = float(sizer["min_qty"])
    price = float(sizer["price"])

    # qty не перевищує кришку та не нижче біржових мінімумів
    assert qty <= qty_cap_floor + 1e-12, f"qty {qty} > cap_floor {qty_cap_floor}"
    assert qty >= min_qty - 1e-12, f"qty {qty} < min_qty {min_qty}"
    # мін-нотіонал також повинен виконуватись
    assert qty * price >= float(sizer["min_notional"]) - 1e-9

    # Перевіримо, що крок дотримано (множник кроку)
    if lot_step > 0:
        steps = round(qty / lot_step)
        assert abs(qty - steps * lot_step) < 1e-9, "qty має бути кратним lot_step"

def test_atr_budget_blocks_when_cap_below_exchange_min(monkeypatch):
    """
    Коли CAP занадто малий (100$ на BTCUSDT), CAP < min_qty => applied=False, reason=cap_below_exchange_min,
    і ордер не будується (order_payload=None).
    """
    monkeypatch.setenv("RISK_MAX_POS_USD", "100")
    prev = _place(
        "BTCUSDT",
        ps_mode="atr_budget",
        atr=100.0,
        tick_value=1.0,
        risk_budget_day_remaining=25.0,
        dd_pct_day=2.0,
    )
    sizer = prev["sizer"]
    meta = sizer.get("atr_budget")
    assert meta is not None, "Очікуємо наявність метаданих ATR-бюджету"
    assert meta["applied"] is False
    assert meta["reason"] == "cap_below_exchange_min"

    # Перевіримо, що payload не побудовано
    assert prev.get("order_payload") is None

def test_atr_budget_bad_inputs(monkeypatch):
    """
    Погані інпути (atr<=0) вимикають ATR-бюджет (applied=False, reason=bad_inputs).
    """
    monkeypatch.setenv("RISK_MAX_POS_USD", "500")  # CAP великий, але atr=0 зламає ATR-бюджет
    prev = _place(
        "BTCUSDT",
        ps_mode="atr_budget",
        atr=0.0,
        tick_value=1.0,
        risk_budget_day_remaining=25.0,
        dd_pct_day=0.0,
    )
    meta = prev["sizer"].get("atr_budget")
    assert meta is not None
    assert meta["applied"] is False
    assert meta["reason"] == "bad_inputs"

def test_qty_never_exceeds_cap(monkeypatch):
    """
    Перевіряємо, що навіть при великих risk_budget та маленькому ATR кількість не перевищує CAP.
    """
    monkeypatch.setenv("RISK_MAX_POS_USD", "150")  # ~ достатньо, але будемо стежити за кришкою
    prev = _place(
        "BTCUSDT",
        ps_mode="atr_budget",
        atr=50.0,
        tick_value=1.0,
        risk_budget_day_remaining=500.0,  # великий бюджет
        dd_pct_day=0.0,
    )
    sizer = prev["sizer"]
    meta = sizer.get("atr_budget")
    assert meta is not None
    if meta["applied"]:
        qty = float(sizer["qty"])
        qty_cap_floor = float(meta["qty_cap_floor"])
        assert qty <= qty_cap_floor + 1e-12, f"qty {qty} > cap_floor {qty_cap_floor}"

def test_kill_switch_blocks_trade(monkeypatch):
    """
    Kill-switch має пріоритет: при наявності run/TRADE_KILLED.flag risk_gate.can_trade=False незалежно від ATR.
    """
    rg = importlib.import_module("core.risk_guard")
    try:
        rg.kill("pytest kill-switch")
        prev = _place(
            "BTCUSDT",
            ps_mode="atr_budget",
            atr=100.0,
            tick_value=1.0,
            risk_budget_day_remaining=1000.0,
            dd_pct_day=0.0,
        )
        gate = prev["risk_gate"]
        assert gate["can_trade"] is False
        # ATR-блок при цьому може бути застосований/не застосований — не критично;
        # головне, що can_trade=False через kill-switch.
        reason = gate["reason"]
        # шукаємо в violations мітку kill_switch
        vio = json.dumps(reason, ensure_ascii=False)
        assert "kill_switch" in vio
    finally:
        # приберемо флаг
        rg.clear_kill()
