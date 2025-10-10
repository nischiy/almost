# utils/exit_adapter.py  (v3)
from __future__ import annotations
import os, json, ssl, time, hmac, hashlib
from urllib import request, parse

BINANCE_FAPI_BASE = os.environ.get("BINANCE_FAPI_BASE", "https://fapi.binance.com")
_API_KEY = os.environ.get("API_KEY","")
_API_SECRET = os.environ.get("API_SECRET","")

def _sign(params: dict) -> bytes:
    p = dict(params)
    p.setdefault("timestamp", int(time.time()*1000))
    p.setdefault("recvWindow", 5000)
    qs = parse.urlencode(p, doseq=True)
    sig = hmac.new(_API_SECRET.encode("utf-8"), qs.encode("utf-8"), hashlib.sha256).hexdigest()
    return (qs + "&signature=" + sig).encode("utf-8")

def _post(path: str, params: dict) -> dict:
    url = BINANCE_FAPI_BASE.rstrip("/") + path
    ctx = ssl.create_default_context()
    data = _sign(params)
    headers = {"X-MBX-APIKEY": _API_KEY, "User-Agent": "exit-adapter/3.0"}
    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req, context=ctx, timeout=15) as r:
            raw = r.read().decode("utf-8")
            try: return json.loads(raw)
            except Exception: return {"raw": raw}
    except Exception as e:
        body = None
        try:
            if hasattr(e, "read"): body = e.read().decode("utf-8")
        except Exception:
            pass
        return {"error": str(e), "body": body}

def _sanitize_exit_payload(d: dict) -> dict:
    out = dict(d)
    t = str(out.get("type","")).upper()

    # For STOP/TP MARKET: Binance requires stopPrice, disallows timeInForce.
    if t in ("STOP_MARKET", "TAKE_PROFIT_MARKET"):
        out.pop("timeInForce", None)
        out.pop("price", None)  # price not used for MARKET variants
        # booleans as strings "true"/"false" are ok; keep closePosition/reduceOnly
        if "stopPrice" not in out or out["stopPrice"] is None:
            raise ValueError("stopPrice required for exit order")

    # Clean Nones
    for k in list(out.keys()):
        if out[k] is None:
            out.pop(k)
    return out

def preview_exits(symbol: str, side_entry: str, sl_price: float|None, tp_price: float|None) -> dict:
    exit_side = "SELL" if side_entry.upper() == "BUY" else "BUY"
    orders = []
    if sl_price:
        orders.append({
            "symbol": symbol,
            "side": exit_side,
            "type": "STOP_MARKET",
            "closePosition": "true",
            "reduceOnly": "true",
            "stopPrice": float(sl_price),
        })
    if tp_price:
        orders.append({
            "symbol": symbol,
            "side": exit_side,
            "type": "TAKE_PROFIT_MARKET",
            "closePosition": "true",
            "reduceOnly": "true",
            "stopPrice": float(tp_price),
        })
    return {"preview": True, "orders": orders}

def send_exits(symbol: str, side_entry: str, sl_price: float|None, tp_price: float|None) -> dict:
    exit_side = "SELL" if side_entry.upper() == "BUY" else "BUY"
    results = []
    for spec in preview_exits(symbol, side_entry, sl_price, tp_price)["orders"]:
        body = _sanitize_exit_payload(spec)
        resp = _post("/fapi/v1/order", body)
        results.append({"request": body, "response": resp})
    return {"preview": False, "results": results}
