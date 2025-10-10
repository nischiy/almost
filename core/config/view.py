from __future__ import annotations
import os
from types import SimpleNamespace
from typing import Any

def _read_any(cfg: Any, lower: str, upper: str, default=None):
    if hasattr(cfg, lower):
        return getattr(cfg, lower)
    if hasattr(cfg, upper):
        return getattr(cfg, upper)
    v = os.getenv(upper)
    if v is None:
        v = os.getenv(lower)
    return default if v is None else v

def _as_bool(v: Any, default: bool = False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "y", "on")

def _as_int(v: Any, default: int | None = None):
    try:
        return int(v)
    except Exception:
        return default

def normalize_config_view(cfg: Any) -> SimpleNamespace:
    """Опційно: якщо потрібно мати 'view' без мутації оригіналу cfg."""
    view = SimpleNamespace()
    view.paper_trading = _as_bool(_read_any(cfg, "paper_trading", "PAPER_TRADING", "1"), True)
    view.trade_enabled = _as_bool(_read_any(cfg, "trade_enabled", "TRADE_ENABLED", "0"), False)
    view.binance_testnet = _as_bool(_read_any(cfg, "binance_testnet", "BINANCE_TESTNET", "false"), False)
    view.pre_flight_skip_api = _as_bool(_read_any(cfg, "pre_flight_skip_api", "PRE_FLIGHT_SKIP_API", "1"), True)
    view.symbol = _read_any(cfg, "symbol", "SYMBOL", "BTCUSDT")
    view.strategy_name = _read_any(cfg, "strategy_name", "STRATEGY_NAME", "ema_rsi_atr")
    view.params_path = _read_any(cfg, "params_path", "PARAMS_PATH", "models/ema_rsi_atr/best_params.json")
    view.RISK_MAX_TRADES_PER_DAY = _as_int(_read_any(cfg, "RISK_MAX_TRADES_PER_DAY", "RISK_MAX_TRADES_PER_DAY", 50), 50)
    base_url = _read_any(cfg, "base_url", "BASE_URL", None)
    if not base_url:
        base_url = os.getenv("BASE_URL_TESTNET" if view.binance_testnet else "BASE_URL_MAINNET")
    if not base_url:
        base_url = "https://testnet.binancefuture.com" if view.binance_testnet else "https://fapi.binance.com"
    view.base_url = base_url
    view._raw = cfg
    return view
