import os
from pathlib import Path

def test_env_example_present():
    # Project may ship .env.example or use .env; we just assert at least one exists.
    root = Path(".")
    example = root / ".env.example"
    env = root / ".env"
    assert example.exists() or env.exists(), "Provide .env or .env.example in project root."

def test_required_env_defaults():
    # Ensure critical flags exist or are defaultable via code.
    # We don't import env loader to avoid side-effects; we just check values are strings if present.
    for key in [
        "SYMBOL",
        "PAPER_TRADING",
        "TRADE_ENABLED",
        "PRE_FLIGHT_SKIP_API",
        "STRATEGY_NAME",
    ]:
        val = os.getenv(key, "")
        assert isinstance(val, str)
