def test_config_loader_callable():
    import core.config.loader as L
    assert hasattr(L, "load_config") and callable(L.load_config)
    try:
        _ = L.load_config()
    except Exception as e:
        raise AssertionError(f"load_config raised: {e}")

