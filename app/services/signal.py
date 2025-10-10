# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import logging
from typing import Any, Dict, Callable, Optional

import pandas as pd

# 1) Джерело дефолтних параметрів (підтримує обидві сигнатури: get_best_params() та get_best_params(name))
try:
    from core.config.best_params import get_best_params  # type: ignore
except Exception as e:
    raise RuntimeError(f"Cannot import core.config.best_params.get_best_params: {e}")

log = logging.getLogger("SignalService")

# === Контракт виходу (decision) ==================================================
# {
#   "side": "BUY" | "SELL" | "HOLD",
#   "size_usd": float | None,
#   "sl": float | None,
#   "tp": float | None,
#   "reason": str,
#   ... (інші ключі — як повертає стратегія)
# }
# ================================================================================

# 2) Регістратор стратегій: ім’я → callable(df, params) -> dict
_STRATEGY_CACHE: Dict[str, Callable[[pd.DataFrame, Dict[str, Any]], Dict[str, Any]]] = {}
_ALIASES = {
    "baseline": "ema_rsi_atr",
    "default": "ema_rsi_atr",
}

def _import_strategy_callable(name: str) -> Callable[[pd.DataFrame, Dict[str, Any]], Dict[str, Any]]:
    """
    Пошук функції стратегії у звичних місцях.
    Очікуваний інтерфейс: def decide(df: DataFrame, params: dict) -> dict
    """
    # a) core.logic.<name>.decide
    try:
        mod = __import__(f"core.logic.{name}", fromlist=["decide"])
        fn = getattr(mod, "decide", None)
        if callable(fn):
            return fn  # type: ignore[return-value]
    except Exception:
        pass

    # b) core.logic.<name>_signal  (старий неймінг)
    try:
        mod = __import__("core.logic", fromlist=[f"{name}_signal"])
        fn = getattr(mod, f"{name}_signal", None)
        if callable(fn):
            return fn  # type: ignore[return-value]
    except Exception:
        pass

    raise KeyError(f"Unknown strategy '{name}': expected core.logic.{name}.decide or core.logic.{name}_signal")


def _select_strategy(name: str) -> Callable[[pd.DataFrame, Dict[str, Any]], Dict[str, Any]]:
    n = (name or "").strip()
    if not n:
        raise KeyError("Strategy name is empty")
    fn = _STRATEGY_CACHE.get(n)
    if fn is None:
        fn = _import_strategy_callable(n)
        _STRATEGY_CACHE[n] = fn
    return fn


# 3) Допоміжні утиліти
def _merge_params(defaults: Dict[str, Any], overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Просте злиття: overrides мають пріоритет над defaults."""
    return {**(defaults or {}), **(overrides or {})}


def _best_params_for(name: str) -> Dict[str, Any]:
    """
    Підтримка двох API:
      - get_best_params(name)
      - get_best_params()
    Якщо функція не приймає аргументів — використаємо безіменні дефолти.
    """
    try:
        return get_best_params(name)  # type: ignore[arg-type]
    except TypeError:
        return get_best_params()      # type: ignore[call-arg]


def _normalize_side(v: Any) -> str:
    """Приводимо будь-які варіанти до BUY/SELL/HOLD."""
    if v is None:
        return "HOLD"
    s = str(v).strip().upper()
    if s in ("BUY", "LONG"):
        return "BUY"
    if s in ("SELL", "SHORT"):
        return "SELL"
    return "HOLD"


def _normalize_decision(raw: Dict[str, Any], fallback_reason: str) -> Dict[str, Any]:
    """
    Нормалізує словник рішення до стабільного контракту (див. верхній блок).
    Зберігає всі невідомі ключі як є.
    """
    out = dict(raw or {})
    side = out.get("side") or out.get("action") or "HOLD"
    out["side"] = _normalize_side(side)
    out.setdefault("reason", fallback_reason)
    if "size_usd" not in out:
        out["size_usd"] = out.get("size") if "size" in out else None
    out.setdefault("sl", None)
    out.setdefault("tp", None)
    return out


# 4) Публічний сервіс (DICT-only для params)
class SignalService:
    """
    Універсальний адаптер стратегій (DICT-only).
    - Ім’я стратегії: params['strategy'] або STRATEGY_NAME (ENV), дефолт: 'ema_rsi_atr'.
    - Підтягує дефолтні параметри (best_params) і зливає з params.
    - Викликає стратегію core.logic.<name>.decide або core.logic.<name>_signal.
    - Повертає decision у стабільному форматі (_normalize_decision).
    """
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.log = logger or logging.getLogger("SignalService")

    def decide(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        # Строгий контракт: лише dict
        if not isinstance(params, dict):
            raise TypeError("SignalService.decide expects params: dict")

        # 1) ім’я стратегії (+аліаси/фолбек)
        raw_name = str(params.get("strategy") or os.getenv("STRATEGY_NAME") or "ema_rsi_atr").strip()
        name = _ALIASES.get(raw_name, raw_name)

        # 2) дефолтні параметри + оверрайди
        try:
            defaults = _best_params_for(name)
        except Exception as e:
            self.log.warning("best_params for %s failed: %s; fallback to empty defaults", name, e)
            defaults = {}
        merged = _merge_params(defaults, params)

        # 3) виклик стратегії (з фолбеком, якщо назва невідома)
        try:
            fn = _select_strategy(name)
        except KeyError:
            if name != "ema_rsi_atr":
                self.log.info("Strategy '%s' not found, falling back to 'ema_rsi_atr'", name)
                name = "ema_rsi_atr"
                fn = _select_strategy(name)
            else:
                raise

        try:
            raw = fn(df, merged)  # очікується dict
            if not isinstance(raw, dict):
                raise TypeError(f"strategy '{name}' returned non-dict: {type(raw)}")
            return _normalize_decision(raw, fallback_reason=name)
        except Exception as e:
            # Не валимо застосунок: фейл стратегії = HOLD
            self.log.error("Strategy '%s' failed: %s", name, e, exc_info=True)
            return {"side": "HOLD", "reason": f"{name}:error", "sl": None, "tp": None, "size_usd": None}
