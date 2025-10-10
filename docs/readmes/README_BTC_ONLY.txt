BTC-only helper

What it does
- Runs quick_check for BTCUSDT 1h 1000 (PnL snapshot)
- Runs quick_sweep only for BTCUSDT across given intervals (default: 15m,1h,4h)

How to use
1) Unzip into repo root (next to the existing 'scripts' folder).
2) Run:
   .\scripts\diagnostics\btc_only.ps1
   # optional:
   .\scripts\diagnostics\btc_only.ps1 -Intervals "1h,4h" -Limit 800
