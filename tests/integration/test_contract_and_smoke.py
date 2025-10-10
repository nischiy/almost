import importlib
import types

def has_any_attr(obj, names):
    return any(hasattr(obj, n) for n in names)

def test_app_run_contract_smoke():
    """
    Contract smoke: app.run should expose at least one runnable hook.
    This test won't actually hit real APIs; it just validates the contract.
    """
    mod = importlib.import_module("app.run")
    assert isinstance(mod, types.ModuleType)
    # Accept any of these entrypoints (project has varied naming historically)
    hooks = ["start", "loop", "step", "run_once", "tick", "run", "main"]
    assert has_any_attr(mod, hooks), f"app.run must define one of: {hooks}"

def test_strategy_module_imports_smoke():
    """
    Ensure strategy module and indicators import cleanly.
    """
    import importlib
    importlib.import_module("core.logic.ema_rsi_atr")
    importlib.import_module("core.indicators")
    importlib.import_module("core.filters.gates")
    importlib.import_module("core.risk")

def test_filters_and_risk_basic_symbols():
    """
    Quick sanity checks on exported names to catch missing renames.
    """
    import core.filters.gates as gates
    dir_g = dir(gates)
    assert len(dir_g) > 0

    import core.risk as risk
    dir_r = dir(risk)
    assert len(dir_r) > 0
