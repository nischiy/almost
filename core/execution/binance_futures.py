from __future__ import annotations
import time, hmac, hashlib, os
from typing import Dict, Any, Optional
import requests

BINANCE_FAPI_BASE = "https://testnet.binancefuture.com" if str(os.getenv("BINANCE_TESTNET","0")).strip() in {"1","true","TRUE","True"} else "https://fapi.binance.com"

API_KEY  = os.getenv("BINANCE_FAPI_KEY", "")
API_SECRET = os.getenv("BINANCE_FAPI_SECRET", "")

def _ts() -> int:
    return int(time.time() * 1000)

def _sign(params: Dict[str, Any]) -> str:
    if not API_SECRET:
        raise RuntimeError("BINANCE_FAPI_SECRET is not set")
    q = "&".join([f"{k}={params[k]}" for k in sorted(params)])
    return hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()

def _headers() -> Dict[str, str]:
    if not API_KEY:
        raise RuntimeError("BINANCE_FAPI_KEY is not set")
    return {"X-MBX-APIKEY": API_KEY, "Content-Type": "application/x-www-form-urlencoded"}

def _get(path: str, params: Dict[str, Any], private: bool=False) -> Any:
    url = BINANCE_FAPI_BASE + path
    if private:
        params["timestamp"] = _ts()
        params["signature"] = _sign(params)
    r = requests.get(url, params=params, headers=_headers() if private else None, timeout=10)
    r.raise_for_status()
    return r.json()

def _post(path: str, params: Dict[str, Any]) -> Any:
    url = BINANCE_FAPI_BASE + path
    params["timestamp"] = _ts()
    params["signature"] = _sign(params)
    r = requests.post(url, data=params, headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()

# ----- Public helpers -----
def ping() -> bool:
    try:
        requests.get(BINANCE_FAPI_BASE + "/fapi/v1/ping", timeout=5)
        return True
    except Exception:
        return False

def exchange_info(symbol: str) -> Any:
    return _get("/fapi/v1/exchangeInfo", {"symbol": symbol}, private=False)

def klines(symbol: str, interval: str, limit: int=500) -> Any:
    return _get("/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit}, private=False)

# ----- Private trading -----
def get_balance(asset: str="USDT") -> Optional[float]:
    data = _get("/fapi/v2/balance", {}, private=True)
    for it in data:
        if it.get("asset") == asset:
            # cross wallet + unrealized notional не додаємо - базовий баланс
            return float(it.get("balance", 0.0))
    return None

def get_position(symbol: str) -> Dict[str, Any]:
    arr = _get("/fapi/v2/positionRisk", {"symbol": symbol}, private=True)
    return arr[0] if arr else {}

def place_order(symbol: str, side: str, quantity: float, order_type: str="MARKET",
                reduce_only: bool=False, price: Optional[float]=None, tp: Optional[float]=None, sl: Optional[float]=None,
                time_in_force: str="GTC", position_side: Optional[str]=None) -> Dict[str, Any]:
    """
    side: BUY/SELL
    order_type: MARKET/LIMIT
    tp/sl: optional (attached as separate OCO-like? Binance USDT-M supports TP/SL as STOP/TAKE_PROFIT - тут робимо прості child ордери якщо задано)
    """
    params = {
        "symbol": symbol,
        "side": side.upper(),
        "type": order_type.upper(),
        "quantity": f"{quantity}",
        "reduceOnly": "true" if reduce_only else "false"
    }
    if position_side:
        params["positionSide"] = position_side
    if order_type.upper() == "LIMIT":
        if price is None:
            raise ValueError("price is required for LIMIT")
        params["price"] = f"{price}"
        params["timeInForce"] = time_in_force

    res = _post("/fapi/v1/order", params)

    # Best-effort TP/SL (optional)
    if tp is not None:
        try:
            _post("/fapi/v1/order", {
                "symbol": symbol,
                "side": "SELL" if side.upper()=="BUY" else "BUY",
                "type": "TAKE_PROFIT_MARKET",
                "stopPrice": f"{tp}",
                "closePosition": "true"
            })
        except Exception:
            pass
    if sl is not None:
        try:
            _post("/fapi/v1/order", {
                "symbol": symbol,
                "side": "SELL" if side.upper()=="BUY" else "BUY",
                "type": "STOP_MARKET",
                "stopPrice": f"{sl}",
                "closePosition": "true"
            })
        except Exception:
            pass

    return res
