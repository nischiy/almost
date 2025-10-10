
# Project Smoke Test Pack

What it covers:
- Indicators contract (EMA/RSI/ATR) and NaN/shape sanity
- Strategy contract: `StrategyParams`, `compute_features`, `generate_signal`
- Risk gate: `can_open_new_trade` keyword-only API
- App import: `from app.run import TraderApp`

How to run (Windows PowerShell, from your repo root where `core/` and `app/` live):
1) Copy the contents of this archive into the repo root (it won't overwrite your source files).
2) Run:
   ```powershell
   python -m pip install pytest -q
   .\run_tests.ps1
   ```

Notes:
- Tests avoid network and don't call `main.py`. They only import modules and run pure functions.
- If a test fails, read the assertion message and open the referenced file.
