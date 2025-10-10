def test_filters_gates_has_callables():
    import core.filters.gates as G
    funcs = [getattr(G, n) for n in dir(G) if callable(getattr(G, n)) and not n.startswith('_')]
    assert funcs, "core.filters.gates should define at least one callable rule"

