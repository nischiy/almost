# Fixpack E — entrypoint passes cfg to TraderApp (2025-09-22)

## What's inside
- `app/entrypoint.py` — detects `TraderApp` constructor signature and passes `cfg` if required. Keeps old behavior if not needed.
- `.env.example` — minimal, safe defaults for clarity.

## How to apply
1) Unzip over your project.
2) Paper run:
   ```powershell
   .\scripts\run_paper.ps1 -ProjectRoot . -Symbol BTCUSDT -Interval 1m
   ```
3) Live (when ready, with keys in .env):
   ```powershell
   .\scripts\run_live.ps1 -ProjectRoot . -Symbol BTCUSDT -Interval 1m
   ```
