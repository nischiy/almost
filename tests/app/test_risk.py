def test_risk_can_open_basic():
    from app.services.risk import RiskService
    r = RiskService()
    ok, reason = r.can_open({"action":"BUY","qty":0.001})
    assert ok is True
    ok2, reason2 = r.can_open({"action":"HOLD","qty":0.001})
    assert ok2 is False and isinstance(reason2, str)

def test_risk_blocks_invalid_action_and_qty():
    from app.services.risk import RiskService
    r = RiskService()
    ok, reason = r.can_open({"action": "INVALID", "qty": 1.0})
    assert ok is False and reason == "unknown_action"
    ok2, reason2 = r.can_open({"action": "BUY", "qty": 0})
    assert ok2 is False and reason2 == "invalid_qty"
