import importlib

def test_risk_can_open_contract():
    mod = importlib.import_module("app.services.risk")
    rs = mod.RiskService()
    ok, reason = rs.can_open({"action":"LONG","qty":1.0})
    assert ok is True and isinstance(reason, str)
    ok2, reason2 = rs.can_open({"action":"HOLD","qty":0})
    assert ok2 is False and isinstance(reason2, str)
