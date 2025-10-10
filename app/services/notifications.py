# -*- coding: utf-8 -*-
from __future__ import annotations
"""
app.services.notifications
--------------------------
Єдина точка мережевої взаємодії з Binance Futures REST:
  - set_leverage_via_rest(symbol, leverage)
  - place_order_via_rest(**payload)
  - get_open_orders(symbol)
  - cancel_order_via_rest(symbol, orderId | origClientOrderId)

Примітки:
  - DRY_RUN_ONLY: для write-операцій (leverage, order, cancel) повертаємо preview і не шлемо.
  - GET openOrders у DRY_RUN дозволено (читання безпечно).
  - Секрети не логуються. В разі потреби JSON-логи пише рівень вище (order_service/exit_manager).
"""

import os
import json
import ssl
import time
import hmac
import hashlib
from urllib import request, parse
from typing import Dict, Any, Optional

BINANCE_FAPI_BASE = os.environ.get("BINANCE_FAPI_BASE", "https://fapi.binance.com")
_API_KEY = os.environ.get("API_KEY", "")
_API_SECRET = os.environ.get("API_SECRET", "")

def _as_bool(v: Optional[str], default: bool=False) -> bool:
    if v is None:
        return default
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "y", "on")

def _is_dry_run() -> bool:
    return _as_bool(os.environ.get("DRY_RUN_ONLY"), True)

def _headers() -> Dict[str, str]:
    return {
        "X-MBX-APIKEY": _API_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "notifications/1.1",
    }

def _sign_params(params: Dict[str, Any]) -> bytes:
    p = dict(params)
    p.setdefault("timestamp", int(time.time() * 1000))
    p.setdefault("recvWindow", 5000)
    qs = parse.urlencode(p, doseq=True)
    sig = hmac.new(_API_SECRET.encode("utf-8"), qs.encode("utf-8"), hashlib.sha256).hexdigest()
    return (qs + "&signature=" + sig).encode("utf-8")

def _do(method: str, path: str, params: Dict[str, Any], *, signed: bool=True) -> Dict[str, Any]:
    url = BINANCE_FAPI_BASE.rstrip("/") + path
    ctx = ssl.create_default_context()
    headers = _headers()
    data = None
    if method in ("POST", "DELETE"):
        data = _sign_params(params) if signed else parse.urlencode(params).encode("utf-8")
    elif method == "GET":
        if signed:
            # signed GET: put signed querystring
            qs = _sign_params(params).decode("utf-8")
            url += ("?" + qs)
        else:
            qs = parse.urlencode(params)
            url += ("?" + qs)
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, context=ctx, timeout=15) as r:
            raw = r.read().decode("utf-8")
            try:
                return json.loads(raw)
            except Exception:
                return {"raw": raw}
    except Exception as e:
        err = {"error": str(e)}
        try:
            if hasattr(e, "read"):
                err["body"] = e.read().decode("utf-8")
        except Exception:
            pass
        return err

# --- Public API -------------------------------------------------------------

def set_leverage_via_rest(symbol: str, leverage: int) -> Dict[str, Any]:
    if _is_dry_run():
        return {"result": "preview", "op": "set_leverage", "symbol": symbol, "leverage": int(leverage)}
    leverage = max(1, int(leverage))
    return _do("POST", "/fapi/v1/leverage", {"symbol": symbol, "leverage": leverage}, signed=True)

def place_order_via_rest(**payload) -> Dict[str, Any]:
    """
    Очікує Binance-compatible поля:
      symbol, side, type, quantity, [price], [timeInForce], [reduceOnly], [newClientOrderId], [stopPrice], [closePosition]
    """
    if _is_dry_run():
        return {"result": "preview", "op": "place_order", "payload": dict(payload)}
    body = dict(payload)
    # normalize booleans to lower-case strings where needed
    if "reduceOnly" in body and isinstance(body["reduceOnly"], bool):
        body["reduceOnly"] = "true" if body["reduceOnly"] else "false"
    if "closePosition" in body and isinstance(body["closePosition"], bool):
        body["closePosition"] = "true" if body["closePosition"] else "false"
    return _do("POST", "/fapi/v1/order", body, signed=True)

def get_open_orders(symbol: str) -> Dict[str, Any] | list:
    """
    Повертає перелік відкритих ордерів для символу.
    Успішний шлях Binance: list[ order, ... ].
    В разі помилок — dict з "error".
    """
    # GET без обмежень у DRY_RUN (читання)
    return _do("GET", "/fapi/v1/openOrders", {"symbol": symbol}, signed=True)

def cancel_order_via_rest(*, symbol: str, orderId: Optional[int]=None,
                          origClientOrderId: Optional[str]=None) -> Dict[str, Any]:
    """
    Скасовує один ордер (SL/TP теж). Не можна передавати одночасно і orderId, і origClientOrderId — достатньо одного.
    """
    if orderId is None and origClientOrderId is None:
        return {"error": "cancel_order requires orderId or origClientOrderId"}
    if _is_dry_run():
        return {
            "result": "preview", "op": "cancel_order",
            "symbol": symbol, "orderId": orderId, "origClientOrderId": origClientOrderId
        }
    params = {"symbol": symbol}
    if orderId is not None:
        params["orderId"] = int(orderId)
    if origClientOrderId is not None:
        params["origClientOrderId"] = str(origClientOrderId)
    return _do("DELETE", "/fapi/v1/order", params, signed=True)
