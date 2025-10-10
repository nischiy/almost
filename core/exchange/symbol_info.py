from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
from decimal import Decimal

def _dec(x: Any) -> Decimal:
    return Decimal(str(x))

@dataclass
class SymbolFilters:
    price_step: Decimal
    qty_step: Decimal
    min_qty: Decimal
    min_notional: Decimal
    max_qty: Optional[Decimal] = None

    # dict-like accessor expected by live code
    def get(self, key: str, default: Any=None) -> Any:
        k = str(key)
        # direct canonical keys first
        mapping = {
            "tick_size": "price_step",
            "price_tick": "price_step",
            "price_step": "price_step",
            "step_size": "qty_step",
            "qty_step": "qty_step",
            "min_qty": "min_qty",
            "minQty": "min_qty",
            "max_qty": "max_qty",
            "maxQty": "max_qty",
            "min_notional": "min_notional",
            "minNotional": "min_notional",
            "notional": "min_notional",
        }
        # normalize to canonical
        target = mapping.get(k, None)
        if target:
            return getattr(self, target, default)
        # fallback: try exact attribute, then case-insensitive __dict__
        if hasattr(self, k):
            return getattr(self, k)
        d = getattr(self, "__dict__", {}) or {}
        if k in d:
            return d[k]
        lower = {str(kk).lower(): vv for kk, vv in d.items()}
        return lower.get(k.lower(), default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "price_step": float(self.price_step),
            "qty_step": float(self.qty_step),
            "min_qty": float(self.min_qty),
            "min_notional": float(self.min_notional),
            "max_qty": (float(self.max_qty) if self.max_qty is not None else None),
        }

def from_exchange_info(symbol_info: Dict[str, Any]) -> SymbolFilters:
    """Parse Binance exchangeInfo symbol entry into SymbolFilters."""
    # defaults
    price_step = _dec("0.01")
    qty_step = _dec("0.001")
    min_qty = _dec("0.0")
    min_notional = _dec("0.0")
    max_qty = None

    for f in (symbol_info or {}).get("filters", []):
        t = f.get("filterType")
        if t == "PRICE_FILTER":
            step = f.get("tickSize") or f.get("tick_size") or f.get("tick")
            if step: price_step = _dec(step)
            min_price = f.get("minPrice")
            max_price = f.get("maxPrice")
            # not stored but harmless if present
        elif t == "LOT_SIZE":
            step = f.get("stepSize") or f.get("step_size")
            if step: qty_step = _dec(step)
            if f.get("minQty"): min_qty = _dec(f["minQty"])
            if f.get("maxQty"): max_qty = _dec(f["maxQty"])
        elif t in ("MIN_NOTIONAL", "MIN_NOTIONAL_V2"):
            if f.get("notional") or f.get("minNotional"):
                min_notional = _dec(f.get("notional") or f.get("minNotional"))
    return SymbolFilters(price_step, qty_step, min_qty, min_notional, max_qty)
