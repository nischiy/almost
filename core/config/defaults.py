from __future__ import annotations
import os
from typing import Any

def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in ('1','true','yes','y','on')

def apply_cfg_defaults(app: Any) -> None:
    """Опційно: доклеїти дефолти у app.cfg/params/config з ENV, якщо атрибутів бракує."""
    cfg = getattr(app, 'cfg', None) or getattr(app, 'params', None) or getattr(app, 'config', None)
    if cfg is None:
        return
    if not hasattr(cfg, 'symbol'):
        setattr(cfg, 'symbol', os.getenv('SYMBOL') or 'BTCUSDT')
    if not hasattr(cfg, 'interval'):
        setattr(cfg, 'interval', os.getenv('INTERVAL') or os.getenv('STRATEGY_INTERVAL') or '1m')
    if not hasattr(cfg, 'max_bars'):
        try: setattr(cfg, 'max_bars', int(os.getenv('MAX_BARS') or os.getenv('HISTORY_BARS') or 1000))
        except Exception: setattr(cfg, 'max_bars', 1000)
    if not hasattr(cfg, 'fee_bps'):
        try: setattr(cfg, 'fee_bps', float(os.getenv('FEE_BPS') or 4))
        except Exception: setattr(cfg, 'fee_bps', 4.0)
    if not hasattr(cfg, 'slip_bps'):
        try: setattr(cfg, 'slip_bps', float(os.getenv('SLIP_BPS') or os.getenv('SLIPPAGE_BPS') or 1))
        except Exception: setattr(cfg, 'slip_bps', 1.0)
    if not hasattr(cfg, 'enabled'):
        setattr(cfg, 'enabled', _to_bool(os.getenv('TRADE_ENABLED')))
    if not hasattr(cfg, 'paper'):
        setattr(cfg, 'paper', _to_bool(os.getenv('PAPER_TRADING') or os.getenv('DRY_RUN')))
    if not hasattr(cfg, 'testnet'):
        setattr(cfg, 'testnet', _to_bool(os.getenv('BINANCE_TESTNET')))
