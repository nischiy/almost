from __future__ import annotations








































































































































































































































import json

# --- Standard imports
import time, csv, os, functools, math, json
from datetime import datetime, UTC
from typing import Any

# === Retry helper ===
def _retry_on_exceptions(retries: int = 3, initial_delay: float = 0.5, backoff: float = 2.0, retry_on: tuple[type[BaseException], ...] = (Exception,)):
    """Retry decorator with exponential backoff."""
    def deco(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last = None
            for attempt in range(1, retries + 1):
                try:
                    return f(*args, **kwargs)
                except retry_on as e:
                    last = e
                    if attempt >= retries:
                        raise
                    time.sleep(delay)
                    delay *= backoff
            raise last  # pragma: no cover
        return wrapper
    return deco

# === Client factory ===
def ensure_client(testnet: bool = False):
    """
    Lazily create python-binance Client using env vars.
    Uses (BINANCE_API_KEY, BINANCE_API_SECRET) or fallbacks.
    """
    from binance.client import Client
    api_key = os.getenv("BINANCE_API_KEY") or os.getenv("BINANCE_FAPI_KEY") or os.getenv("API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET") or os.getenv("BINANCE_FAPI_SECRET") or os.getenv("API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError("Missing API keys for live trading")
    return Client(api_key, api_secret, testnet=testnet)

# === Exchange info (filters) ===
@_retry_on_exceptions(retries=4, initial_delay=0.3, backoff=2.0, retry_on=(Exception,))
def fetch_exchange_info_cached(client: Any, symbol: str) -> dict[str, float]:
    """Return {price_step, qty_step, min_qty, min_notional} for symbol via client.futures_exchange_info()."""
    info = client.futures_exchange_info()
    sym = next((s for s in info.get("symbols", []) if s.get("symbol") == symbol), None)
    if not sym:
        raise RuntimeError(f"symbol {symbol} not found in exchangeInfo")
    price_step = qty_step = min_qty = min_notional = 0.0
    for f in sym.get("filters", []):
        t = f.get("filterType")
        if t == "PRICE_FILTER":
            price_step = float(f.get("tickSize") or f.get("tick_size") or 0)
        elif t == "LOT_SIZE":
            qty_step = float(f.get("stepSize") or f.get("step_size") or 0)
            min_qty = float(f.get("minQty") or f.get("min_qty") or 0)
        elif t in ("MIN_NOTIONAL", "NOTIONAL"):
            min_notional = float(f.get("minNotional") or f.get("notional") or 0)
    return {"price_step": price_step or 0.0, "qty_step": qty_step or 0.0, "min_qty": min_qty or 0.0, "min_notional": min_notional or 0.0}

# === Order logging ===
def log_order(order: dict, tag: str = "orders") -> None:
    """Append order dict to logs/orders/YYYY-MM-DD.csv (creates file with header if needed)."""
    try:
        d = datetime.now(UTC).date().isoformat()
        path = os.path.join("logs", tag)
        os.makedirs(path, exist_ok=True)
        fn = os.path.join(path, f"{d}.csv")
        keys = ["time_utc","clientOrderId","symbol","side","type","status","origQty","executedQty","price","raw"]
        exists = os.path.exists(fn)
        with open(fn, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            if not exists:
                w.writeheader()
            row = {k: order.get(k, "") for k in keys}
            row["time_utc"] = datetime.now(UTC).isoformat()
            try:
                row["raw"] = json.dumps(order, ensure_ascii=False)
            except Exception:
                row["raw"] = str(order)
            w.writerow(row)
    except Exception:
        pass  # never зриваємо виконання через лог

# === Entry / Protective orders ===
@_retry_on_exceptions(retries=4, initial_delay=0.5, backoff=2.0, retry_on=(Exception,))
def place_entry(cli, symbol: str, side: str, qty: float, price: float | None, client_order_id: str | None = None) -> dict:
    """
    Create a MARKET or LIMIT entry order on USDT-m futures.
    side: 'BUY' / 'SELL'
    """
    params = {"symbol": symbol, "side": side, "quantity": qty}
    if client_order_id:
        params["newClientOrderId"] = client_order_id
    if price is None:
        params["type"] = "MARKET"
    else:
        params["type"] = "LIMIT"
        params["timeInForce"] = "GTC"
        params["price"] = price
    res = cli.futures_create_order(**params)
    try:
        log_order(res)
    except Exception:
        pass
    return res

def place_protective(cli, symbol: str, side: str, sl: float | None, tp: float | None, qty: float, base_client_id: str = "") -> dict:
    """
    Place STOP_MARKET (SL) and TAKE_PROFIT_MARKET (TP) with reduceOnly=True.
    """
    res: dict[str, Any] = {}
    ro = True
    opp_side = "SELL" if side == "BUY" else "BUY"
    if sl:
        cid = (base_client_id + "_SL")[:32] if base_client_id else None
        @_retry_on_exceptions(retries=3, initial_delay=0.5, backoff=2.0, retry_on=(Exception,))
        def _place_sl():
            return cli.futures_create_order(
                symbol=symbol, side=opp_side, type="STOP_MARKET",
                stopPrice=sl, closePosition=False, reduceOnly=ro,
                quantity=qty, newClientOrderId=cid
            )
        try:
            res["sl"] = _place_sl()
            log_order(res["sl"])
        except Exception as e:
            res["sl_err"] = str(e)
    if tp:
        cid = (base_client_id + "_TP")[:32] if base_client_id else None
        @_retry_on_exceptions(retries=3, initial_delay=0.5, backoff=2.0, retry_on=(Exception,))
        def _place_tp():
            return cli.futures_create_order(
                symbol=symbol, side=opp_side, type="TAKE_PROFIT_MARKET",
                stopPrice=tp, closePosition=False, reduceOnly=ro,
                quantity=qty, newClientOrderId=cid
            )
        try:
            res["tp"] = _place_tp()
            log_order(res["tp"])
        except Exception as e:
            res["tp_err"] = str(e)
    return res