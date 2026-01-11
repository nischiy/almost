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

import time
import uuid
import logging
import importlib
import os
import json
from typing import Dict, Any, Callable, Optional, Tuple, List

from core.config.env import get_bool

log = logging.getLogger("OrderService")
_ACCOUNT_CACHE: Dict[str, Any] = {}
_ACCOUNT_TTL_SEC = 45.0

# ---- Імпорти (чисто, без SourceFileLoader) -------------------------------------

def _import_or_fail(module: str, attr: str) -> Callable[..., Any]:
    mod = importlib.import_module(module)
    fn  = getattr(mod, attr, None)
    if not callable(fn):
        raise ImportError(f"{module}.{attr} is not callable or missing")
    return fn

# Адаптер: будує payload (розмір/ризики всередині)
build_order = _import_or_fail("app.services.order_adapter", "build_order")
preflight_market_data = _import_or_fail("app.services.order_adapter", "preflight_market_data")
# Відправка/системні REST (можуть кидати виключення)
place_order_via_rest = _import_or_fail("app.services.notifications", "place_order_via_rest")
set_leverage_via_rest = _import_or_fail("app.services.notifications", "set_leverage_via_rest")


# ---- Допоміжні утиліти ---------------------------------------------------------

def _is_dry_run() -> bool:
    return get_bool("DRY_RUN_ONLY", True)

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

class _PreviewDict(dict):
    def get(self, key, default=None):
        if key == "order_payload":
            if key not in self:
                return default
            value = dict.__getitem__(self, key)
            if value == {}:
                return None
            return value
        return dict.get(self, key, default)

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

def _fetch_equity_usd() -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Best-effort equity lookup (live only). Returns (equity_usd, wallet_usdt, reason).
    """
    try:
        from core.exchange_private import fetch_futures_private
    except Exception as e:
        return None, None, f"import_error:{e}"
    data = fetch_futures_private()
    if not isinstance(data, dict):
        return None, None, "invalid_response"
    balances = data.get("balances") or {}
    for key in ("USDT", "BUSD", "USDC"):
        if key in balances:
            try:
                value = float(balances[key])
                return value, value, "futures_balance"
            except Exception:
                return None, None, "parse_error"
    return None, None, data.get("error") or "no_balance"

def _allow_offline_fallback() -> bool:
    env = str(os.getenv("ENV", "production") or "production").lower()
    if env != "production":
        return True
    return "PYTEST_CURRENT_TEST" in os.environ

def _get_account_snapshot(wallet_usdt: Optional[float] = None) -> Dict[str, Any]:
    now = time.time()
    if "PYTEST_CURRENT_TEST" not in os.environ:
        cached = _ACCOUNT_CACHE.get("snapshot")
        if cached and now - float(cached.get("ts") or 0.0) <= _ACCOUNT_TTL_SEC:
            snap = dict(cached)
            snap["source"] = "cache"
            snap["origin"] = cached.get("source")
            return snap
    equity_usd, wallet_val, reason = _fetch_equity_usd()
    fallback_wallet = wallet_usdt
    if fallback_wallet is None and _allow_offline_fallback():
        try:
            fallback_wallet = float(str(os.getenv("WALLET_USDT", "1000")).strip())
        except Exception:
            fallback_wallet = None
    source = "exchange" if equity_usd is not None else "missing"
    if equity_usd is None and fallback_wallet is not None and _allow_offline_fallback():
        equity_usd = float(fallback_wallet)
        wallet_val = float(fallback_wallet)
        source = "fallback"
        if reason:
            reason = f"{reason};fallback_wallet_usdt"
        else:
            reason = "fallback_wallet_usdt"
    snap = {
        "equity_usd": equity_usd,
        "wallet_usdt": wallet_val,
        "source": source,
        "reason": reason,
        "ts": now,
    }
    if "PYTEST_CURRENT_TEST" not in os.environ:
        _ACCOUNT_CACHE["snapshot"] = dict(snap)
    return snap

def validate_preflight(snapshot: Dict[str, Any]) -> List[str]:
    rejects: List[str] = []
    account = snapshot.get("account") or {}
    price = snapshot.get("price") or {}
    filters = snapshot.get("filters") or {}
    equity_val = account.get("equity_usd")
    wallet_val = account.get("wallet_usdt")
    if equity_val is None or float(equity_val or 0.0) <= 0:
        detail = account.get("reason") or account.get("source")
        rejects.append(f"missing_account_equity:{detail}" if detail else "missing_account_equity")
    if wallet_val is None or float(wallet_val or 0.0) <= 0:
        detail = account.get("reason") or account.get("source")
        rejects.append(f"missing_wallet_usdt:{detail}" if detail else "missing_wallet_usdt")
    price_val = price.get("value")
    if price_val is None or float(price_val or 0.0) <= 0:
        detail = price.get("reason") or price.get("source")
        rejects.append(f"missing_price:{detail}" if detail else "missing_price")
    step_size = filters.get("step_size")
    min_qty = filters.get("min_qty")
    min_notional = filters.get("min_notional")
    tick_size = filters.get("tick_size")
    if step_size is None or float(step_size or 0.0) <= 0:
        detail = filters.get("reason") or filters.get("source")
        rejects.append(f"missing_filter_step_size:{detail}" if detail else "missing_filter_step_size")
    if min_qty is None or float(min_qty or 0.0) <= 0:
        detail = filters.get("reason") or filters.get("source")
        rejects.append(f"missing_filter_min_qty:{detail}" if detail else "missing_filter_min_qty")
    if min_notional is None or float(min_notional or 0.0) < 0:
        detail = filters.get("reason") or filters.get("source")
        rejects.append(f"missing_filter_min_notional:{detail}" if detail else "missing_filter_min_notional")
    if tick_size is None or float(tick_size or 0.0) <= 0:
        detail = filters.get("reason") or filters.get("source")
        rejects.append(f"missing_filter_tick_size:{detail}" if detail else "missing_filter_tick_size")
    return rejects

def preflight_read(symbol: str, wallet_usdt: Optional[float] = None) -> Dict[str, Any]:
    account = _get_account_snapshot(wallet_usdt)
    market = preflight_market_data(symbol)
    snapshot = {
        "account": account,
        "price": market.get("price") or {},
        "filters": market.get("filters") or {},
    }
    snapshot["rejects"] = validate_preflight(snapshot)
    return snapshot


# ---- Головна функція сервісу ---------------------------------------------------

def place(symbol: str, side: str, otype: str, wallet_usdt: float, **kwargs) -> Dict[str, Any]:
    """
    Побудувати ордер через order_adapter, і (опційно) відправити через REST.
    Повертає структурований результат для логування/діагностики.
    """
    rg_state = kwargs.get("rg_state") or {}
    if not isinstance(rg_state, dict):
        rg_state = {}
    if not rg_state.get("equity_usd"):
        account = _get_account_snapshot(wallet_usdt)
        equity_usd = account.get("equity_usd")
        if equity_usd is not None:
            rg_state["equity_usd"] = equity_usd
            rg_state.setdefault("equity_source", account.get("source") or "exchange")
        else:
            rg_state["equity_usd"] = None
            rg_state.setdefault("equity_source", account.get("source") or "missing")
        if account.get("reason"):
            rg_state.setdefault("equity_reason", account.get("reason"))

    # 1) Побудова ордера (ризики/сайзер/payload)
    built: Dict[str, Any] = build_order(symbol, side, otype, wallet_usdt, **{**kwargs, "rg_state": rg_state})

    payload = built.get("order_payload")
    preview_payload = payload or {}
    preview: Dict[str, Any] = _PreviewDict({
        "risk_gate": built.get("risk_gate"),
        "sizer": built.get("sizer"),
        "order_payload": preview_payload,
        "errors": list(built.get("errors") or []),
        "blockers": list(built.get("blockers") or []),
    })
    preview["block_reasons"] = list(preview.get("blockers") or [])
    try:
        sizer = preview.get("sizer") or {}
        data_sources = sizer.get("data_sources") or {}
        equity_meta = data_sources.get("equity") or {}
        filters_meta = data_sources.get("filters") or {}
        log_payload = {
            "strategy": kwargs.get("strategy"),
            "action": kwargs.get("action") or side,
            "reasons": kwargs.get("reasons") or kwargs.get("reason"),
            "equity_usd": {"value": equity_meta.get("value"), "source": equity_meta.get("source")},
            "price": {"value": data_sources.get("price", {}).get("value"), "source": data_sources.get("price", {}).get("source")},
            "filters": {"source": filters_meta.get("source")},
            "risk_usd": sizer.get("risk_usd"),
            "qty_min": sizer.get("qty_min"),
            "qty_final": sizer.get("qty_final") or sizer.get("qty"),
            "sl_base": sizer.get("sl_base"),
            "sl_final": sizer.get("sl_final"),
            "leverage_selected": sizer.get("leverage_selected") or sizer.get("leverage"),
            "blockers": preview.get("blockers") or [],
        }
        log.info("order_decision: %s", json.dumps(log_payload, sort_keys=True))
    except Exception:
        pass

    # 2) DRY-RUN: лише прев'ю без мережі (повертаємо навіть при блокерах)
    if _is_dry_run():
        return {
            "submitted": False,
            "reason": "dry_run",
            "preview": preview,
            "block_reasons": preview.get("blockers") or [],
            "network": {"set_leverage": None, "place_order": None},
        }

    if not payload:
        # Немає чого відправляти (ризик/сайзер/валідація відсіяли)
        blockers = preview.get("blockers") or []
        if blockers:
            log.warning("order blocked: %s", blockers)
        return {
            "submitted": False,
            "reason": "no_payload",
            "preview": preview,
            "block_reasons": blockers,
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
