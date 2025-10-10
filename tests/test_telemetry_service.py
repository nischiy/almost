
import pandas as pd
from app.services.telemetry import TelemetryService

def test_telemetry_smoke(tmp_path):
    tel = TelemetryService()
    df = pd.DataFrame({"open_time":[pd.Timestamp("2025-01-01", tz="UTC")], "open":[1.0], "high":[1.0], "low":[1.0], "close":[1.0], "volume":[1.0], "close_time":[pd.Timestamp("2025-01-01", tz="UTC")]})
    tel.snapshot(df)  # should not raise
    tel.decision({"time": df.iloc[0]["open_time"], "side":"FLAT","reason":"test","rsi":50.0,"ema_fast":1,"ema_slow":1,"atr":0.1,"sl":0,"tp":0})
    tel.health(ok=True, msg="ok")  # should not raise
