# Fixpack D — Stable entrypoint + run scripts (2025‑09‑22)

## What's inside
- `app/entrypoint.py` — unified, import-safe launcher. No network calls at import time. Picks `loop`/`run`/`run_once` automatically.
- `scripts/run_paper.ps1` — paper mode, trading disabled.
- `scripts/run_live.ps1` — live mode, trading enabled; add `-Testnet` switch if needed.
- `scripts/run_pytest_fast.ps1` — quick pytest run.

## How to use
Paper:
```powershell
.\scripts
un_paper.ps1 -ProjectRoot . -Symbol BTCUSDT -Interval 1m
```

Live (mainnet):
```powershell
.\scripts
un_live.ps1 -ProjectRoot . -Symbol BTCUSDT -Interval 1m
```

Live (testnet):
```powershell
.\scripts
un_live.ps1 -ProjectRoot . -Testnet -Symbol BTCUSDT -Interval 1m
```

Pytest:
```powershell
.\scripts
un_pytest_fast.ps1 -ProjectRoot .
```

This keeps your existing `main.py` intact while providing a stable launch path for operations and CI.
