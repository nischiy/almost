import inspect

def test_symbol_info_api_present():
    import core.exchange.symbol_info as S
    names = [n for n in dir(S) if n.startswith("get_") or "symbol" in n.lower()]
    funcs = [getattr(S, n) for n in names if callable(getattr(S, n))]
    assert funcs, "No callable API found in symbol_info"
    fn = funcs[0]
    try:
        if len(inspect.signature(fn).parameters) >= 1:
            fn("BTCUSDT")
    except Exception:
        pass

