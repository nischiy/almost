
from pathlib import Path
from app.services.execution import ExecutorService

def test_executor_paper_writes_csv(monkeypatch, tmp_path):
    # Ensure paper mode
    monkeypatch.setenv("PAPER_TRADING","1")
    monkeypatch.setenv("TRADE_ENABLED","0")
    exe = ExecutorService("BTCUSDT")
    decision = {"side":"LONG","price":100.0,"sl":99.0,"tp":101.5}
    exe.place(decision)
    # Check files
    d = list((Path("logs")/"orders").glob("*/orders.csv"))
    assert d, "orders.csv not written"
