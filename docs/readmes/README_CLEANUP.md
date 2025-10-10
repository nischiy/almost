
# Strategy Cleanup (v4)
- Fix: no duplicate deletions; safe deletion with -ErrorAction SilentlyContinue
- Shows final files in core\logic after cleanup
- Adds small diagnostic script (below) to scan for stale imports (optional)

## Run
Preview:
powershell -ExecutionPolicy Bypass -File .\scripts\diagnostics\list_strategies.ps1 -ProjectRoot .
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_strategies.ps1 -ProjectRoot . -Keep ema_rsi_atr.py -WhatIf

Apply:
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_strategies.ps1 -ProjectRoot . -Keep ema_rsi_atr.py

If you want, I can provide a follow-up patch to update imports from `core.strategy` or `core.logic.logic` to `core.logic.ema_rsi_atr`.
