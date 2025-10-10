def test_execution_modules_importable():
    import core.execution.binance_exec as spot
    import core.execution.binance_futures as fut
    assert len([n for n in dir(spot) if not n.startswith('_')]) > 0
    assert len([n for n in dir(fut) if not n.startswith('_')]) > 0

