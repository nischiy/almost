
"""
Position Sizer — математика визначення розміру позиції.
SRP: обчислює qty від ризику/ATR/леverage, приводить до біржових кроків.
"""
from typing import Dict, Any
from decimal import Decimal

def atr_based_qty(balance: float, risk_pct: float, atr: float, price: float, *, leverage: float = 1.0) -> float:
    """Простий приклад: позиція за ATR (класична формула Келлі-подібна).
    qty ~= (balance * risk_pct * leverage) / (atr * price)
    """
    if atr <= 0 or price <= 0: 
        return 0.0
    return float((balance * risk_pct * leverage) / (atr * price))

def quantize_qty(qty: float, step_size: float, min_qty: float) -> float:
    if qty <= 0:
        return 0.0
    steps = int(qty / step_size)
    q = steps * step_size
    return q if q >= min_qty else 0.0

def size(decision: Dict[str, Any], *, balance: float, risk: Dict[str, Any], metrics: Dict[str, Any], symbol_info) -> float:
    """Головна точка входу.
    decision: з поля може надходити бажана вага/фіксована кількість.
    risk: {"risk_pct": 0.01, "leverage": 2, ...}
    metrics: {"atr": ..., "price": ...}
    symbol_info: очікується об'єкт з stepSize/minQty або подібними властивостями.
    """
    if "qty" in decision and decision["qty"]:
        qty = float(decision["qty"])
    else:
        atr = float(metrics.get("atr") or 0.0)
        price = float(metrics.get("price") or 0.0)
        qty = atr_based_qty(balance, float(risk.get("risk_pct", 0.01)), atr, price, leverage=float(risk.get("leverage", 1.0)))
    step = float(getattr(symbol_info, "stepSize", getattr(symbol_info, "step_size", 0.001)) or 0.001)
    minq = float(getattr(symbol_info, "minQty", getattr(symbol_info, "min_qty", 0.0)) or 0.0)
    return quantize_qty(qty, step, minq)
