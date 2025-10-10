import importlib
import types
import pytest

CANDIDATES = [
    ("app.entrypoint", "main"),
    ("app.app", "main"),
    ("app.bootstrap", "main"),
]

def _find_callable():
    found = []
    for mod_name, func_name in CANDIDATES:
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        fn = getattr(mod, func_name, None)
        if callable(fn):
            found.append((mod_name, func_name))
    return found

def test_entrypoint_callable_present():
    '''
    Checks that at least one entrypoint exists: app.entrypoint:main, app.app:main, or app.bootstrap:main.
    If none are found, this is the direct cause of "silent" start without logs.
    '''
    found = _find_callable()
    assert found, (
        "No callable main() found. "
        "Add main() to app/entrypoint.py (or app/app.py, app/bootstrap.py)."
    )
