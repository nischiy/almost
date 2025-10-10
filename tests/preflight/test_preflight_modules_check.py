
import types
import builtins
import importlib
import pytest

from tools.preflight import preflight_all as PF


class _Dummy:
    __version__ = "1.2.3"


def test_check_modules_happy(monkeypatch):
    # Reduce required modules to a minimal, controlled set
    monkeypatch.setattr(PF, "REQUIRED_MODULES", [
        ("python-binance", "binance", True),
        ("pandas", "pandas", True),
        ("orjson", "orjson", False),
    ], raising=True)

    real_import = builtins.__import__

    def fake_import(name, *a, **kw):
        if name in {"binance", "pandas", "orjson"}:
            return _Dummy()
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    out = PF.check_modules()
    assert out["ok"] is True
    names = {x["import"] for x in out["modules"]}
    assert {"binance", "pandas", "orjson"}.issubset(names)
