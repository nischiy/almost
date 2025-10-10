def test_risk_can_open_basic():
    from app.services.risk import RiskService
    r = RiskService()
    ok, reason = r.can_open({"action":"LONG","qty":0.001})
    assert ok is True
    ok2, reason2 = r.can_open({"action":"HOLD","qty":0.001})
    assert ok2 is False and isinstance(reason2, str)
