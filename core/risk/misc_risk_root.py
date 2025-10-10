from __future__ import annotations
from typing import Dict, Tuple

def can_open(decision: Dict) -> Tuple[bool, str]:
    """Basic guard: allow only LONG/SHORT with qty>0 if provided."""
    action = decision.get("action")
    if action not in ("LONG", "SHORT"):
        return False, "hold_or_unknown_action"
    qty = decision.get("qty", 1.0)
    try:
        qty = float(qty)
    except Exception:
        qty = 0.0
    if qty <= 0:
        return False, "qty<=0"
    return True, ""
