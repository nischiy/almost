from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional
from core.config.env import parse_bool, get_env

# =====================
# Config dataclass
# =====================
@dataclass
class Config:
    ENV: str = "production"
    PAPER_TRADING: bool = True
    TRADE_ENABLED: bool = False
    BINANCE_TESTNET: bool = False

    EXCHANGE: str = "binance_futures"
    SYMBOL: str = "BTCUSDT"
    INTERVAL: str = "1m"
    HTF_INTERVAL: str = "15m"
    QUOTE_ASSET: str = "USDT"

    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""

    LOG_DIR: str = "logs"

# ---- Centralized ENV normalization & singleton config ----
_SYNONYMS = {
    "BINANCE_API_KEY": ["BINANCE_API_KEY", "API_KEY"],
    "BINANCE_API_SECRET": ["BINANCE_API_SECRET", "API_SECRET"],
    "PAPER_TRADING": ["PAPER_TRADING", "PAPER", "PAPER_MODE"],
    "TRADE_ENABLED": ["TRADE_ENABLED", "TRADE", "ENABLE_TRADING"],
    "BINANCE_TESTNET": ["BINANCE_TESTNET", "TESTNET"],
    "SYMBOL": ["SYMBOL", "PAIR"],
    "INTERVAL": ["INTERVAL", "TF", "TIMEFRAME"],
    "LOG_DIR": ["LOG_DIR", "LOGS_DIR"],
}

def normalize_env(environ: Optional[dict] = None) -> None:
    """
    Normalize environment variables to a canonical schema in os.environ.
    This is the ONLY place that 'analyzes' .env — other modules should just read canonical keys.
    """
    e = dict(os.environ)
    if environ:
        e.update(environ)

    # Forward mapping: set canonical keys from the first non-empty alias
    for canonical, keys in _SYNONYMS.items():
        val = None
        for k in keys:
            v = e.get(k)
            if v is not None and str(v).strip() != "":
                val = str(v)
                break
        if val is not None:
            os.environ[canonical] = val

    # Bidirectional backfill for API keys to support legacy readers
    if os.environ.get("BINANCE_API_KEY") and not os.environ.get("API_KEY"):
        os.environ["API_KEY"] = os.environ["BINANCE_API_KEY"]
    if os.environ.get("BINANCE_API_SECRET") and not os.environ.get("API_SECRET"):
        os.environ["API_SECRET"] = os.environ["BINANCE_API_SECRET"]
    if os.environ.get("API_KEY") and not os.environ.get("BINANCE_API_KEY"):
        os.environ["BINANCE_API_KEY"] = os.environ["API_KEY"]
    if os.environ.get("API_SECRET") and not os.environ.get("BINANCE_API_SECRET"):
        os.environ["BINANCE_API_SECRET"] = os.environ["API_SECRET"]

    # Canonical defaults (only if not present)
    os.environ.setdefault("PAPER_TRADING", "1")
    os.environ.setdefault("TRADE_ENABLED", "0")
    os.environ.setdefault("BINANCE_TESTNET", "0")
    os.environ.setdefault("SYMBOL", "BTCUSDT")
    os.environ.setdefault("INTERVAL", "1m")
    os.environ.setdefault("LOG_DIR", "logs")

# Singleton holder for cached Config
_CONFIG_SINGLETON: Optional[Config] = None

def load_config() -> Config:
    """Build Config from (already normalized) environment."""
    return Config(
        ENV=get_env("ENV", "production"),
        PAPER_TRADING=parse_bool(get_env("PAPER_TRADING", "1")),
        TRADE_ENABLED=parse_bool(get_env("TRADE_ENABLED", "0")),
        BINANCE_TESTNET=parse_bool(get_env("BINANCE_TESTNET", "0")),

        EXCHANGE=get_env("EXCHANGE", "binance_futures"),
        SYMBOL=get_env("SYMBOL", "BTCUSDT"),
        INTERVAL=get_env("INTERVAL", "1m"),
        HTF_INTERVAL=get_env("HTF_INTERVAL", "15m"),
        QUOTE_ASSET=get_env("QUOTE_ASSET", "USDT"),

        BINANCE_API_KEY=get_env("BINANCE_API_KEY", ""),
        BINANCE_API_SECRET=get_env("BINANCE_API_SECRET", ""),

        LOG_DIR=get_env("LOG_DIR", "logs"),
    )

def get_config() -> Config:
    global _CONFIG_SINGLETON
    if _CONFIG_SINGLETON is None:
        normalize_env()
        _CONFIG_SINGLETON = load_config()
    return _CONFIG_SINGLETON

__all__ = ["Config", "normalize_env", "load_config", "get_config"]
