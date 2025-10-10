def test_best_params_module_imports():
    import core.config.best_params as BP
    ok = False
    if hasattr(BP, "BEST_PARAMS"):
        assert isinstance(BP.BEST_PARAMS, (dict, list))
        ok = True
    if hasattr(BP, "get_best_params") and callable(BP.get_best_params):
        res = BP.get_best_params()
        assert isinstance(res, (dict, list))
        ok = True
    assert ok, "best_params must expose BEST_PARAMS or get_best_params()"

