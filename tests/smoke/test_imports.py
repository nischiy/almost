# smoke: imports should be cheap and side-effect free
def test_import_app():
    import app.run as ar
    assert hasattr(ar, "TraderApp")
def test_import_core():
    import core, core.indicators, core.precision
    assert True
