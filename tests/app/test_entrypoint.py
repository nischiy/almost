def test_entrypoint_main_runs_once(monkeypatch):
    import sys
    # Monkeypatch TraderApp.run_once to avoid heavy work
    import app.run as runmod
    called = {"flag": False}
    def fake_run_once(self):
        called["flag"] = True
    monkeypatch.setattr(runmod.TraderApp, "run_once", fake_run_once, raising=True)

    import app.entrypoint as e
    argv = ["app.entrypoint","--once","--paper","--enabled","--symbol","BTCUSDT","--strategy","ema_rsi_atr","--sleep","1"]
    monkeypatch.setenv("PAPER_TRADING","1")
    monkeypatch.setenv("TRADE_ENABLED","1")
    monkeypatch.setenv("SYMBOL","BTCUSDT")
    monkeypatch.setenv("STRATEGY_NAME","ema_rsi_atr")

    monkeypatch.setattr(sys, "argv", argv)
    rc = e.main()
    assert rc == 0
    assert called["flag"] is True
