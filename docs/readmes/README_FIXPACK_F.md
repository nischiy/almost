# Fixpack F — Robust config loader (2025-09-22)

Provides `core/config/loader.py` with a `Config` dataclass exposing the fields expected by your app:
- `base_url` (auto-picked futures base, testnet-aware or via `BINANCE_FAPI_BASE`)
- `max_bars` (default 1000)
- plus paper/enabled/testnet, symbol/interval, timeouts, fee/slippage, paths.

Your existing `core/config/__init__.py` will import this loader automatically.

## How to apply
1) Unzip over your project.
2) Paper run again:
   ```powershell
   .\scripts\run_paper.ps1 -ProjectRoot . -Symbol BTCUSDT -Interval 1m
   ```
3) If you use testnet:
   ```powershell
   .\scripts\run_live.ps1 -ProjectRoot . -Testnet -Symbol BTCUSDT -Interval 1m
   ```
