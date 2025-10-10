README_TESTS_FIX.md
=====================

This patch prevents the test suite from *appearing to freeze* by skipping long-running
end-to-end/integration tests by default and marking them as `slow` and `integration`.

- Updated `pytest.ini` to add: `-m "not slow and not integration"`.
- Marked heavy modules with `pytestmark = [pytest.mark.slow, pytest.mark.integration]`:
  - tests/test_integration_xt_backtest.py
  - tests/test_integration_xt_backtest_pro.py
  - tests/test_pipeline_end_to_end.py
- Added helper script: `scripts/run_pytest_fast.ps1`

To run the full suite including slow tests:
    pytest -q -m "slow or integration"

Or just a single heavy test with a timeout on Windows PowerShell:
    pytest tests/test_pipeline_end_to_end.py -q -m slow --maxfail=1

You can temporarily override skipping via:
    $env:PYTEST_ADDOPTS = '-q -m "slow or integration"'
