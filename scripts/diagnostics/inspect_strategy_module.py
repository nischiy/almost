"""
Inspect what callables exist in the strategy module.
Run from project root:
  python scripts/diagnostics/inspect_strategy_module.py
"""
import os, sys, importlib, inspect

# Ensure project root on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

mod = importlib.import_module("core.logic.ema_rsi_atr")
print("Module:", mod.__file__)

names = [n for n in dir(mod) if not n.startswith("_")]
funcs = [(n, getattr(mod, n)) for n in names if callable(getattr(mod, n))]
classes = [(n, c) for n,c in funcs if inspect.isclass(c)]
funcs = [(n, f) for n,f in funcs if not inspect.isclass(f)]

print("\nFunctions:")
for n,f in funcs:
    try:
        sig = str(inspect.signature(f))
    except Exception:
        sig = "(?)"
    print(f" - {n}{sig}")

print("\nClasses:")
for n,c in classes:
    methods = [m for m in dir(c) if callable(getattr(c,m)) and not m.startswith('_')]
    print(f" - {n}  methods={methods}")
