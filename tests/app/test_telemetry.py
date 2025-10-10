from pathlib import Path

def test_health_writes_jsonl(tmp_path):
    from core.telemetry.health import log_health
    log_health(ok=True, msg="unit-test")
    # check that logs/health/YYYY-MM-DD/health.jsonl exists
    # date folder is created under current working dir (isolated by fixture)
    base = Path("logs") / "health"
    assert base.exists()
    # find any jsonl files inside date dirs
    found = False
    for d in base.iterdir():
        if d.is_dir():
            f = d / "health.jsonl"
            if f.exists():
                found = True
                break
    assert found, "health.jsonl not found"
