import os
import sys
import subprocess
import pytest

def test_run_module_produces_output(monkeypatch):
    '''
    Ensures that `python -m app.run` does not exit silently:
    - returns code 0 within <= 10s
    - prints something to stdout or stderr
    If there is no output, the test fails with an explanatory message.
    '''
    env = os.environ.copy()
    env.setdefault("PAPER_TRADING", "1")
    env.setdefault("TRADE_ENABLED", "0")
    env.setdefault("SYMBOL", "BTCUSDT")

    cmd = [sys.executable, "-m", "app.run"]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, env=env, timeout=10
        )
    except subprocess.TimeoutExpired:
        pytest.fail("`python -m app.run` hung (timeout 10s).")

    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()

    assert proc.returncode == 0, (
        f"`python -m app.run` exited with code {proc.returncode}. "
        f"STDERR: {err[:400]}"
    )
    assert out or err, (
        "Process exited without any output. "
        "This indicates missing explicit startup logging or main()."
    )
