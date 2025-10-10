def test_risk_root_has_can_open_like():
    import core.risk.misc_risk_root as R
    names = [n for n in dir(R) if "can_open" in n or "allow" in n]
    assert names, "risk root should expose guard function(s)"

