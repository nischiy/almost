def test_positions_portfolio_importable():
    import core.positions.portfolio as P
    assert len([n for n in dir(P) if not n.startswith('_')]) > 0

