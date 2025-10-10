# Fixpack C — Futures time endpoint (2025‑09‑22)

This patch replaces any leftover `spot` time endpoint `/api/v3/time` with the correct `futures` endpoint `/fapi/v1/time`.

## How to apply
1) Unzip over your project root.
2) Run:
   ```powershell
   python .\scripts\patch_public_time.py .
   ```
3) Smoke:
   ```powershell
   .\scripts\smoke_run.ps1 -ProjectRoot . -Symbol BTCUSDT -Interval 1m
   ```

Patcher is idempotent and writes `.bak_time` backups.
