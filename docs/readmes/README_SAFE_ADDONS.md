# Safe Add-ons (non-breaking)

This bundle adds **read-only** preflight diagnostics and **opt-in** log rotation.
Nothing here places orders or changes your existing trading flow.

## What’s inside
- `scripts/diagnostics/preflight_v2.py` — read-only checks: ping, server time drift, symbol filters, min notional/qty estimate.
- `utils/logrotate.py` — size/time-based log cleanup (only when run).
- `scripts/tools/safe_ops.ps1` — helper PowerShell commands.

## How to use
**Preflight (read-only):**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\tools\safe_ops.ps1 preflight
```
Environment (optional):
- `SYMBOL` (default: BTCUSDT)
- `PREFLIGHT_MAX_DRIFT_MS` (default: 1500)
- `BINANCE_FAPI_BASE` (default: https://fapi.binance.com)

**Rotate logs (opt-in):**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\tools\safe_ops.ps1 rotate-logs logs 100 14
```
This keeps total size under 100 MB and removes files older than 14 days.
