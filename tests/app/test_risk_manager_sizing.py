import math

from app.services.order_adapter import build_order


def _set_env(monkeypatch, **values):
    for key, value in values.items():
        monkeypatch.setenv(key, str(value))


def test_risk_manager_tightens_sl_for_min_notional(monkeypatch):
    _set_env(
        monkeypatch,
        RISK_PER_TRADE_PCT=1,
        OFFLINE_PRICE_BTCUSDT=100,
        OFFLINE_MIN_QTY_BTCUSDT=0.001,
        OFFLINE_STEP_SIZE_BTCUSDT=0.1,
        OFFLINE_MIN_NOTIONAL_BTCUSDT=100,
        OFFLINE_TICK_SIZE_BTCUSDT=0.1,
        MAX_MARGIN_UTIL_PCT=30,
        MAX_LEVERAGE=10,
        MIN_SL_TICKS=10,
    )
    result = build_order(
        "BTCUSDT",
        "BUY",
        "MARKET",
        wallet_usdt=100,
        rg_state={"equity_usd": 100, "equity_source": "exchange"},
        entry=100,
        sl=95,
    )
    sizer = result["sizer"]
    assert result["blockers"] == []
    assert math.isclose(sizer["qty_min"], 1.0)
    assert math.isclose(sizer["sl_final"], 99.0)
    assert math.isclose(sizer["risk_usd"], 1.0)
    assert sizer["leverage_selected"] == 4


def test_risk_manager_rejects_too_tight_sl(monkeypatch):
    _set_env(
        monkeypatch,
        RISK_PER_TRADE_PCT=0.5,
        OFFLINE_PRICE_BTCUSDT=100,
        OFFLINE_MIN_QTY_BTCUSDT=0.001,
        OFFLINE_STEP_SIZE_BTCUSDT=0.1,
        OFFLINE_MIN_NOTIONAL_BTCUSDT=100,
        OFFLINE_TICK_SIZE_BTCUSDT=0.1,
        MIN_SL_TICKS=10,
    )
    result = build_order(
        "BTCUSDT",
        "BUY",
        "MARKET",
        wallet_usdt=100,
        rg_state={"equity_usd": 100, "equity_source": "exchange"},
        entry=100,
        sl=90,
    )
    assert "min_notional_requires_too_tight_sl" in result["blockers"]
    assert result["order_payload"] is None


def test_risk_manager_leverage_selection(monkeypatch):
    _set_env(
        monkeypatch,
        RISK_PER_TRADE_PCT=1,
        OFFLINE_PRICE_BTCUSDT=100,
        OFFLINE_MIN_QTY_BTCUSDT=0.001,
        OFFLINE_STEP_SIZE_BTCUSDT=0.1,
        OFFLINE_MIN_NOTIONAL_BTCUSDT=200,
        OFFLINE_TICK_SIZE_BTCUSDT=0.1,
        MAX_MARGIN_UTIL_PCT=10,
        MAX_LEVERAGE=25,
        MIN_SL_TICKS=1,
    )
    result = build_order(
        "BTCUSDT",
        "BUY",
        "MARKET",
        wallet_usdt=100,
        rg_state={"equity_usd": 100, "equity_source": "exchange"},
        entry=100,
        sl=99,
    )
    assert result["sizer"]["leverage_selected"] == 20

    _set_env(
        monkeypatch,
        RISK_PER_TRADE_PCT=1,
        OFFLINE_MIN_NOTIONAL_BTCUSDT=100,
        MAX_MARGIN_UTIL_PCT=30,
        MAX_LEVERAGE=10,
    )
    result = build_order(
        "BTCUSDT",
        "BUY",
        "MARKET",
        wallet_usdt=10000,
        rg_state={"equity_usd": 10000, "equity_source": "exchange"},
        entry=100,
        sl=99,
    )
    assert result["sizer"]["leverage_selected"] == 1
