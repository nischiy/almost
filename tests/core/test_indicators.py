import pandas as pd

def _find_indicators_module():
    try:
        import core.indicators as mod
        return mod
    except Exception:
        try:
            import core.indicators.indicators as mod
            return mod
        except Exception:
            import importlib
            return importlib.import_module("core.indicators")

def test_indicators_basic():
    mod = _find_indicators_module()
    s = pd.Series([1,2,3,4,5], dtype=float)
    if hasattr(mod, "ema"):
        e = mod.ema(s, 2)
        assert len(e) == len(s)
    if hasattr(mod, "rsi"):
        r = mod.rsi(s, 2)
        assert len(r) == len(s)
    df = pd.DataFrame({"high":[2,3,4], "low":[1,2,3], "close":[1.5,2.5,3.5]})
    if hasattr(mod, "atr"):
        a = mod.atr(df, 2)
        assert len(a) == len(df)

