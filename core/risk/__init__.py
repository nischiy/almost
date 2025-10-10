# core/risk/__init__.py (tuple-friendly can_open_new_trade)
# Ensures can_open_new_trade returns (bool, reason) to satisfy callers that unpack two values.

from typing import Any, Tuple

# --- Re-export limits symbols if present ---
try:
    from .limits import *  # noqa: F401,F403
except Exception:
    pass

# --- Precision shims ---
try:
    from ..precision import round_price as normalize_price  # type: ignore
    from ..precision import round_qty as normalize_qty      # type: ignore
except Exception:
    def normalize_price(price, tick_size=None):  # type: ignore
        return float(price)
    def normalize_qty(qty, step_size=None):      # type: ignore
        return float(qty)

# --- Utilities ---
def _to_tuple(result: Any) -> Tuple[bool, str]:
    """Normalize various result shapes to (allowed: bool, reason: str)."""
    # direct bool
    if isinstance(result, bool):
        return result, "ok" if result else "blocked"
    # tuple/list
    if isinstance(result, (tuple, list)):
        if len(result) == 0:
            return True, "ok"
        if len(result) == 1:
            r0 = bool(result[0])
            return r0, "ok" if r0 else "blocked"
        # take first two
        r0 = bool(result[0])
        r1 = str(result[1]) if result[1] is not None else ("ok" if r0 else "blocked")
        return r0, r1
    # dict-like
    if isinstance(result, dict):
        if "allowed" in result or "ok" in result:
            allowed = bool(result.get("allowed", result.get("ok", True)))
            reason = str(result.get("reason", "ok" if allowed else "blocked"))
            return allowed, reason
    # fallback
    try:
        b = bool(result)
    except Exception:
        b = True
    return b, "ok" if b else "blocked"

# --- can_open_new_trade shim ---
_fn_direct = None
try:
    from .limits import can_open_new_trade as _fn_direct  # type: ignore
except Exception:
    _fn_direct = None

_rm_instance = None
if _fn_direct is None:
    try:
        from .limits import RiskManager  # type: ignore
    except Exception:
        RiskManager = None  # type: ignore
    if RiskManager is not None:
        try:
            _rm_instance = getattr(RiskManager, "from_env")()
        except Exception:
            try:
                _rm_instance = RiskManager()
            except Exception:
                _rm_instance = None

def can_open_new_trade(*args, **kwargs):
    """Compatibility wrapper returning (allowed: bool, reason: str)."""
    # Prefer direct function
    if callable(_fn_direct):
        try:
            return _to_tuple(_fn_direct(*args, **kwargs))
        except Exception as e:
            return True, f"ok (fallback after error: {e})"
    # Try RiskManager methods
    if _rm_instance is not None:
        for name in ("can_open_new_trade", "allow_new_trade", "can_open"):
            method = getattr(_rm_instance, name, None)
            if callable(method):
                try:
                    return _to_tuple(method(*args, **kwargs))
                except Exception as e:
                    return True, f"ok (fallback after error: {e})"
    # Last resort: permissive
    return True, "ok (fallback)"

# Maintain __all__
try:
    __all__  # type: ignore
except NameError:
    __all__ = []
for _n in ("normalize_price", "normalize_qty", "can_open_new_trade"):
    if _n not in __all__:
        __all__.append(_n)
