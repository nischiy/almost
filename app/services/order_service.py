# -*- coding: utf-8 -*-
from __future__ import annotations
"""
Centralized Order Service (production-ready)

Роль:
  - Приймає рішення (side/type/size тощо) від стратегії/раннера.
  - Через order_adapter.build_order(...) рахує розмір/ризики та збирає order_payload.
  - В DRY-RUN режимі повертає прев'ю без мережевих викликів.
  - У live режимі (DRY_RUN_ONLY=0) виконує мережеві виклики:
      1) set_leverage_via_rest(symbol, leverage) — опційно
      2) place_order_via_rest(**payload)         — відправка

Публічний API (стабільний):
    place(symbol, side, otype, wallet_usdt, **kwargs) -> dict
      kwargs прокидаються в order_adapter.build_order(...):
        desired_pos_usdt, risk_margin_fraction, preferred_max_leverage,
        price (для LIMIT), reduce_only, client_order_id, rg_state, ...

ENV:
    DRY_RUN_ONLY = 1|0|true|false|on|off  (default: 1 → ніколи не шлемо в мережу)

Вихід:
    {
      "submitted": bool,
      "reason": "dry_run" | "no_payload" | "invalid_payload" | "sent" | "send_failed",
      "preview": { "risk_gate": ..., "sizer": ..., "order_payload": ..., "errors": [...] },
      "network": { "set_leverage": <resp|None>, "place_order": <resp|None> }
    }
"""

import os
import time
import uuid
import logging
import importlib
from typing import Dict, Any, Callable, Optional

log = logging.getLogger("OrderService")

# ---- Імпорти (чисто, без SourceFileLoader) -------------------------------------

def _import_or_fail(module: str, attr: str) -> Callable[..., Any]:
    mod = importlib.import_module(module)
    fn  = getattr(mod, attr, None)
    if not callable(fn):
        raise ImportError(f"{module}.{attr} is not callable or missing")
    return fn

# Адаптер: будує payload (розмір/ризики всередині)
build_order = _import_or_fail("app.services.order_adapter", "build_order")
# Відправка/системні REST (можуть кидати виключення)
place_order_via_rest = _import_or_fail("app.services.notifications", "place_order_via_rest")
set_leverage_via_rest = _import_or_fail("app.services.notifications", "set_leverage_via_rest")


# ---- Допоміжні утиліти ---------------------------------------------------------

def _as_bool(v: Optional[str], default: bool = True) -> bool:
    if v is None:
        return default
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "y", "on")

def _is_dry_run() -> bool:
    return _as_bool(os.getenv("DRY_RUN_ONLY", "1"), True)

def _ensure_client_order_id(payload: Dict[str, Any]) -> None:
    """
    Ідемпотентність: якщо немає client_order_id — згенерувати стабільний.
    """
    if not payload.get("client_order_id"):
        payload["client_order_id"] = f"cl-{uuid.uuid4().hex[:16]}"

def _validate_payload(payload: Dict[str, Any]) -> Optional[str]:
    """
    Базова валідація перед відправкою.
    Очікуємо мінімум: symbol, side, type; для LIMIT — price.
    """
    req = ("symbol", "side", "type")
    miss = [k for k in req if not payload.get(k)]
    if miss:
        return f"missing required fields: {','.join(miss)}"
    if str(payload.get("type", "")).upper() == "LIMIT" and not payload.get("price"):
        return "missing price for LIMIT order"
    return None

def _retry_call(fn: Callable[..., Any],
                *,
                attempts: int = 3,
                base_delay: float = 0.5,
                max_delay: float = 4.0,
                on_retry_log: str = "") -> Any:
    """
    Проста стратегія ретраїв з експоненційною паузою.
    Перехоплює будь-який Exception, логгує WARN і повторює.
    Кидає останній виняток, якщо всі спроби вичерпано.
    """
    delay = base_delay
    last_exc: Optional[BaseException] = None
    for i in range(1, attempts + 1):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if i < attempts:
                if on_retry_log:
                    log.warning("%s — retry %d/%d in %.2fs (err: %s)", on_retry_log, i, attempts, delay, e)
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
            else:
                break
    assert last_exc is not None
    raise last_exc


# ---- Головна функція сервісу ---------------------------------------------------

def place(symbol: str, side: str, otype: str, wallet_usdt: float, **kwargs) -> Dict[str, Any]:
    """
    Побудувати ордер через order_adapter, і (опційно) відправити через REST.
    Повертає структурований результат для логування/діагностики.
    """
    # 1) Побудова ордера (ризики/сайзер/payload)
    built: Dict[str, Any] = build_order(symbol, side, otype, wallet_usdt, **kwargs)

    preview: Dict[str, Any] = {
        "risk_gate": built.get("risk_gate"),
        "sizer": built.get("sizer"),
        "order_payload": built.get("order_payload"),
        "errors": list(built.get("errors") or []),
    }

    payload = preview["order_payload"]
    if not payload:
        # Немає чого відправляти (ризик/сайзер/валідація відсіяли)
        return {
            "submitted": False,
            "reason": "no_payload",
            "preview": preview,
            "network": {"set_leverage": None, "place_order": None},
        }

    # 2) DRY-RUN: лише прев'ю без мережі
    if _is_dry_run():
        return {
            "submitted": False,
            "reason": "dry_run",
            "preview": preview,
            "network": {"set_leverage": None, "place_order": None},
        }

    # 3) Live path: валідація + ідемпотентність + мережа
    # 3.1) Валідація мінімального контракту
    err = _validate_payload(payload)
    if err:
        preview["errors"].append(f"invalid_payload: {err}")
        return {
            "submitted": False,
            "reason": "invalid_payload",
            "preview": preview,
            "network": {"set_leverage": None, "place_order": None},
        }

    # 3.2) Ідемпотентність
    _ensure_client_order_id(payload)

    net = {"set_leverage": None, "place_order": None}

    # 3.3) Виставити плече (необов'язково)
    leverage = payload.pop("leverage", None)
    if leverage:
        try:
            net["set_leverage"] = _retry_call(
                lambda: set_leverage_via_rest(symbol, int(leverage)),
                attempts=3,
                base_delay=0.6,
                max_delay=3.0,
                on_retry_log=f"set_leverage({symbol},{leverage}) failed",
            )
        except Exception as e:
            msg = f"set_leverage_error: {e}"
            preview["errors"].append(msg)
            log.warning(msg)

    # 3.4) Відправити ордер
    try:
        net["place_order"] = _retry_call(
            lambda: place_order_via_rest(**payload),
            attempts=3,
            base_delay=0.6,
            max_delay=3.0,
            on_retry_log=f"place_order({payload.get('symbol')},{payload.get('side')},{payload.get('type')}) failed",
        )
        submitted = True
        reason = "sent"
    except Exception as e:
        preview["errors"].append(f"place_order_error: {e}")
        submitted = False
        reason = "send_failed"

    return {
        "submitted": submitted,
        "reason": reason,
        "preview": preview,
        "network": net,
    }
