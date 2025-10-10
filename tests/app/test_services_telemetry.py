import importlib
import pandas as pd

def test_telemetry_service_api(df_klines):
    mod = importlib.import_module("app.services.telemetry")
    tel = mod.TelemetryService()
    tel.health(ok=True, msg="ok")
    tel.snapshot(df_klines.head(2))
    tel.decision({"a":1})
