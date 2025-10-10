# -*- coding: utf-8 -*-
from __future__ import annotations
import inspect
from app.run import TraderApp

print("TraderApp class:", TraderApp)
sig = None
try:
    sig = inspect.signature(TraderApp)
    print("__init__ signature:", sig)
except Exception as e:
    print("inspect.signature failed:", e)

app = None
try:
    app = TraderApp  # just reference
    print("Has loop? ", hasattr(TraderApp, "loop"))
    print("Has run? ", hasattr(TraderApp, "run"))
    print("Has run_once? ", hasattr(TraderApp, "run_once"))
except Exception as e:
    print("Introspection error:", e)
