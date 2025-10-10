from __future__ import annotations
from typing import Any

def _wrap_zero_one_any(fn, app):
    try:
        from inspect import signature
        sig = signature(fn)
        req = [p for p in sig.parameters.values() 
               if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) and p.default is p.empty]
        nreq = len(req)
    except Exception:
        nreq = 0
    if nreq <= 0:  return lambda *args, **kwargs: fn()
    if nreq == 1:  return lambda *args, **kwargs: fn(app)
    return lambda *args, **kwargs: fn(*args, **kwargs)

def patch_can_open_new_trade(app: Any) -> None:
    """Опційно: шим-обгортки для вирівнювання can_open_new_trade (інстанс/модуль)."""
    fn = getattr(app, 'can_open_new_trade', None)
    if callable(fn):
        setattr(app, 'can_open_new_trade', _wrap_zero_one_any(fn, app))
    rg = None
    try:
        import core.risk_guard as rg  # type: ignore
    except Exception:
        try:
            import core.risk as rg  # type: ignore
        except Exception:
            rg = None
    if rg is not None and hasattr(rg, 'can_open_new_trade') and callable(getattr(rg, 'can_open_new_trade')):
        setattr(rg, 'can_open_new_trade', _wrap_zero_one_any(getattr(rg, 'can_open_new_trade'), app))
