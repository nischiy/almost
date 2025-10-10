
import json
from types import SimpleNamespace
from app.services.market_data import HttpMarketData

def test_market_data_uses_public_api(monkeypatch):
    sample = [
        [1735689600000,"100","101","99","100.5","12","1735689660000","0","0","0","0","0"],
        [1735689660000,"100.5","101.2","100.2","101.0","10","1735689720000","0","0","0","0","0"],
    ]

    class FakeResp:
        def __init__(self, payload): self._p = payload
        def raise_for_status(self): pass
        def json(self): return self._p

    def fake_get(url, timeout=10):
        assert "/fapi/v1/klines" in url
        return FakeResp(sample)

    monkeypatch.setattr("requests.get", fake_get)
    md = HttpMarketData(base_url="https://fapi.binance.com")
    df = md.get_klines("BTCUSDT","1m",limit=2)
    assert len(df) == 2
    assert set(df.columns) == {"open_time","open","high","low","close","volume","close_time"}
