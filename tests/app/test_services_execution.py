import importlib, os, glob, shutil
from pathlib import Path

def test_executor_service_writes_orders_csv(tmp_path, monkeypatch):
    mod = importlib.import_module("app.services.execution")

    # ensure logs dir inside tmp
    monkeypatch.setenv("PAPER_TRADING", "1")
    monkeypatch.setenv("TRADE_ENABLED", "0")
    monkeypatch.chdir(tmp_path)

    exe = mod.ExecutorService(symbol="BTCUSDT")
    exe.place({"action":"LONG","price":100.0,"qty":1.0})

    # find orders.csv under logs/orders/<date>.csv
    d = list(Path("logs").glob("orders/*/*.csv"))
    assert d, "orders.csv not written"
