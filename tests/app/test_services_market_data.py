import importlib, json

def test_http_market_data_get_klines_mock(monkeypatch):
    md = importlib.import_module("app.services.market_data")

    sample = [
        [0, "100", "101", "99", "100.5", "1.0", 0, "0", 0, "0", "0", "0"],
        [1, "100.5", "102", "100", "101.0", "2.0", 0, "0", 0, "0", "0", "0"],
    ]
    def fake_http(url, params, headers=None, timeout=15):
        return json.dumps(sample)

    monkeypatch.setattr(md, "_http_get", fake_http)
    o = md.HttpMarketData()
    df = o.get_klines("BTCUSDT", "1m", limit=2)
    # normalized columns
    for c in ["open_time","open","high","low","close","volume","close_time"]:
        assert c in df.columns
    assert len(df) == 2
