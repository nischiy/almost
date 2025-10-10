from __future__ import annotations
import os, math, json, ssl, urllib.request
from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any
BINANCE_FAPI_BASE = os.environ.get("BINANCE_FAPI_BASE", "https://fapi.binance.com")
_ctx = ssl.create_default_context()
def _http_json(url: str, timeout: int = 10) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "position-sizer/1.1"})
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx) as r:
        return json.loads(r.read().decode("utf-8"))
def public_price(symbol: str) -> float:
    return float(_http_json(f"{BINANCE_FAPI_BASE}/fapi/v1/ticker/price?symbol={symbol}")["price"])
def public_filters(symbol: str) -> Dict[str, dict]:
    info = _http_json(f"{BINANCE_FAPI_BASE}/fapi/v1/exchangeInfo?symbol={symbol}")
    for s in info.get("symbols", []):
        if s.get("symbol") == symbol:
            return {f["filterType"]: f for f in s.get("filters", [])}
    return {}
@dataclass
class SizerConfig:
    risk_margin_fraction: float = 0.20
    preferred_max_leverage: int = 10
    fee_bps: float = 5.0
    extra_buffer_pct: float = 0.02
    desired_pos_usdt: Optional[float] = None
@dataclass
class SizerResult:
    qty: float; leverage: int; notional: float; margin_used: float; margin_cap: float
    min_leverage_needed: int; price: float; lot_step: float; min_qty: float; min_notional: float
    meta: Dict[str, Any]
def _round_up(x: float, step: float) -> float:
    if step <= 0: return x
    return math.ceil(x / step) * step
def compute_qty_leverage(symbol: str, wallet_usdt: float,
    get_price: Callable[[str], float] = public_price,
    get_filters: Callable[[str], Dict[str, dict]] = public_filters,
    cfg: SizerConfig = SizerConfig()) -> SizerResult:
    px = float(get_price(symbol)); fmap = get_filters(symbol) or {}
    lot = fmap.get("LOT_SIZE", {}); step = float(lot.get("stepSize", "0.0")) if lot else 0.0
    min_qty = float(lot.get("minQty", "0.0")) if lot else 0.0
    min_notional = float((fmap.get("MIN_NOTIONAL") or {}).get("notional", "0.0")) if fmap else 0.0
    target_usdt = max(cfg.desired_pos_usdt, min_notional) if cfg.desired_pos_usdt is not None else max(min_notional, min_qty*px)
    raw_qty = max(target_usdt/px if px>0 else 0.0, min_qty); qty = _round_up(raw_qty, step) if step>0 else raw_qty
    notional = qty * px
    fee_frac = cfg.fee_bps/10000.0; buffer_frac = cfg.extra_buffer_pct
    margin_cap = wallet_usdt * max(min(cfg.risk_margin_fraction,1.0),0.0)
    denom = margin_cap / (1.0 + fee_frac + buffer_frac) if margin_cap>0 else 0.0
    min_lev = int(max(1, math.ceil(notional/denom))) if denom>0 else 999999
    lev = int(max(1, min(max(1, cfg.preferred_max_leverage), max(1, min_lev))))  # fixed
    margin_used = notional/lev * (1.0 + fee_frac + buffer_frac)
    return SizerResult(qty, lev, notional, margin_used, margin_cap, min_lev, px, step, min_qty, min_notional,
        {"notes": ["Qty rounded up to step","Ensured >= minQty and >= MIN_NOTIONAL",
                   "Leverage = minimal to fit margin cap, then capped by preferred_max_leverage"]})
