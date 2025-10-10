import inspect

def test_execution_has_callable_place_like():
    from app.services import execution as exmod
    cls = None
    for name in ("ExecutorService","ExecutionService","TradeExecutor","Executor"):
        c = getattr(exmod, name, None)
        if inspect.isclass(c):
            cls = c; break
    assert cls is not None, "No execution class found in app.services.execution"
    # constructor flexibility
    try:
        inst = cls(None, symbol="BTCUSDT")
    except TypeError:
        try:
            inst = cls("BTCUSDT")
        except TypeError:
            inst = cls()
    # method present
    place = getattr(inst, "place", None) or getattr(inst, "place_order", None) or getattr(inst, "execute", None)
    assert callable(place), "Execution service lacks place/place_order/execute"
    # should not raise
    place({"action":"LONG","price":100.0,"qty":0.001})
