import json
import pandas as pd
import types

def test_http_market_data_public_rest(monkeypatch):
    from app.services import market_data as md

    # mock HTTP response from Binance /api/v3/klines
    sample = [
        [1727130000000,"100","101","99","100.5","10","1727130059999","1000","10","5","500","0"],
        [1727130060000,"100.5","102","100","101.5","12","1727130119999","1100","12","6","600","0"],
    ]
    def fake_http_get(url, params, headers=None, timeout=15):
        return json.dumps(sample)

    monkeypatch.setattr(md, "_http_get", fake_http_get)

    h = md.HttpMarketData()
    df = h.get_klines("BTCUSDT", "1m", limit=2)
    assert isinstance(df, pd.DataFrame)
    for col in ("time","open","high","low","close","volume"):
        assert col in df.columns
    assert len(df) == 2
