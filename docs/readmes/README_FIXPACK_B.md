# Fixpack B — Ping endpoint + Console encoding (2025‑09‑22)

## What's inside
- `scripts/patch_public_ping.py` — finds erroneous `/api/v3/ping` usages and replaces with correct futures endpoint `/fapi/v1/ping`.
- `scripts/patch_mojibake_dash.py` — normalizes mdash (`—`) and common mojibake (`вЂ”`) to ASCII `-` in Python sources to keep console logs clean.
- `scripts/smoke_run.ps1` — quick paper-mode run helper.

## How to apply
1. Unzip over your project root.
2. Run ping patch:
   ```powershell
   python .\scripts\patch_public_ping.py .
   ```
3. Normalize dashes in log strings:
   ```powershell
   python .\scripts\patch_mojibake_dash.py .
   ```
4. Quick smoke:
   ```powershell
   .\scripts\smoke_run.ps1 -ProjectRoot . -Symbol BTCUSDT -Interval 1m
   ```

Both patch scripts are idempotent and create `.bak_*` backups next to modified files.
