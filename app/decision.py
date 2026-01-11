from __future__ import annotations

from typing import Any, Dict

_HOLD_ALIASES = {"HOLD", "FLAT", "NONE", "NOOP"}


def normalize_side(value: Any) -> str:
    if value is None:
        return "HOLD"
    side = str(value).strip().upper()
    if side in _HOLD_ALIASES:
        return "HOLD"
    if side in {"BUY", "LONG"}:
        return "BUY"
    if side in {"SELL", "SHORT"}:
        return "SELL"
    return "UNKNOWN"


def normalize_decision(raw: Dict[str, Any] | None, *, fallback_reason: str | None = None) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(raw or {})
    side = normalize_side(out.get("side") or out.get("action") or "HOLD")
    out["side"] = side
    out["action"] = side
    if fallback_reason and "reason" not in out:
        out["reason"] = fallback_reason
    if "reasons" not in out and "reason" in out:
        out["reasons"] = [out["reason"]]
    return out
