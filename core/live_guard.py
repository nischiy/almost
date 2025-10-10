from .risk import can_open_new_trade

def guard_before_entry(equity_fetcher):
    # patched: build required kwargs for risk gate from equity_fetcher
    try:
        _eq_src = equity_fetcher() if callable(equity_fetcher) else equity_fetcher
        _es = None; _rpnl = None
        if isinstance(_eq_src, dict):
            _es = _eq_src.get('equity_series'); _rpnl = _eq_src.get('realized_pnl')
        elif isinstance(_eq_src, tuple) and len(_eq_src) >= 2:
            _es, _rpnl = _eq_src[0], _eq_src[1]
        else:
            _es = getattr(_eq_src, 'equity_series', None)
            _rpnl = getattr(_eq_src, 'realized_pnl', None)
        ok, reason = can_open_new_trade(equity_series=_es, realized_pnl=_rpnl)
    except Exception:
        ok, reason = can_open_new_trade()

    return ok, reason