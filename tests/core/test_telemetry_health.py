def test_telemetry_health_importable_and_callable(tmp_path, monkeypatch):
    from core.telemetry.health import log_health
    monkeypatch.chdir(tmp_path)
    log_health(ok=True, msg="core-telemetry-smoke")

