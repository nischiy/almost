def test_filters_presets_importable_and_evaluable(monkeypatch, tmp_path):
    from core.filters_pkg.sets import evaluate_preset
    monkeypatch.chdir(tmp_path)  # isolate logs; snapshots may be absent
    ok, msgs = evaluate_preset("LONG", preset="SESSION_ONLY")
    assert isinstance(ok, bool)
    assert isinstance(msgs, list)
