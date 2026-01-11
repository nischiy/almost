from __future__ import annotations
import os
from typing import Any
from core.config.env import parse_bool, get_env

def apply_cfg_defaults(app: Any) -> None:
    """Опційно: доклеїти дефолти у app.cfg/params/config з ENV, якщо атрибутів бракує."""
    cfg = getattr(app, 'cfg', None) or getattr(app, 'params', None) or getattr(app, 'config', None)
    if cfg is None:
        return
    if not hasattr(cfg, 'symbol'):
        setattr(cfg, 'symbol', get_env('SYMBOL') or 'BTCUSDT')
    if not hasattr(cfg, 'interval'):
        setattr(cfg, 'interval', get_env('INTERVAL') or get_env('STRATEGY_INTERVAL') or '1m')
    if not hasattr(cfg, 'max_bars'):
        try: setattr(cfg, 'max_bars', int(get_env('MAX_BARS') or get_env('HISTORY_BARS') or 1000))
        except Exception: setattr(cfg, 'max_bars', 1000)
    if not hasattr(cfg, 'fee_bps'):
        try: setattr(cfg, 'fee_bps', float(get_env('FEE_BPS') or 4))
        except Exception: setattr(cfg, 'fee_bps', 4.0)
    if not hasattr(cfg, 'slip_bps'):
        try: setattr(cfg, 'slip_bps', float(get_env('SLIP_BPS') or get_env('SLIPPAGE_BPS') or 1))
        except Exception: setattr(cfg, 'slip_bps', 1.0)
    if not hasattr(cfg, 'enabled'):
        setattr(cfg, 'enabled', parse_bool(get_env('TRADE_ENABLED')))
    if not hasattr(cfg, 'paper'):
        setattr(cfg, 'paper', parse_bool(get_env('PAPER_TRADING') or get_env('DRY_RUN')))
    if not hasattr(cfg, 'testnet'):
        setattr(cfg, 'testnet', parse_bool(get_env('BINANCE_TESTNET')))
