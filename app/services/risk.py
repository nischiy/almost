# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Tuple


class RiskService:
    """Minimal, deterministic risk gate for tests and basic use."""

    def __init__(self) -> None:
        self._hold_actions = {"HOLD", "FLAT", "NONE", "NOOP"}
        self._trade_actions = {"BUY", "SELL", "LONG", "SHORT"}

    def can_open(self, decision: Dict[str, Any]) -> Tuple[bool, str]:
        if not isinstance(decision, dict):
            return False, "decision_not_dict"

        action = decision.get("action") or decision.get("side") or "HOLD"
        action = str(action).strip().upper()
        if action in self._hold_actions:
            return False, "hold_action"
        if action not in self._trade_actions:
            return False, "unknown_action"

        qty = decision.get("qty")
        if qty is None:
            return False, "missing_qty"
        try:
            qty_val = float(qty)
        except Exception:
            return False, "invalid_qty"
        if qty_val <= 0:
            return False, "invalid_qty"

        return True, "ok"
