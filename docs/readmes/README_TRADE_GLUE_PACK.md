# Trade Glue Pack v1 (add-only)
Purpose: quick trigger for a one-shot trade (preview or live) using our adapters.

Files:
- scripts/diagnostics/trade_once.py  → Python entrypoint (path-robust)
- scripts/tools/trade.ps1            → PowerShell helper

Preview (default DRY_RUN_ONLY=1):
```powershell
$env:WALLET_USDT=103; $env:SYMBOL="BTCUSDT"
$env:RISK_MARGIN_FRACTION=0.2; $env:PREFERRED_MAX_LEVERAGE=10
powershell -ExecutionPolicy Bypass -File .\scripts\tools\trade.ps1 BUY MARKET
powershell -ExecutionPolicy Bypass -File .\scripts\tools\trade.ps1 SELL LIMIT 120000
```

Live (start on testnet!):
```powershell
$env:BINANCE_FAPI_BASE="https://testnet.binancefuture.com"
$env:API_KEY="..."; $env:API_SECRET="..."; $env:DRY_RUN_ONLY=0
$env:WALLET_USDT=103; $env:SYMBOL="BTCUSDT"
powershell -ExecutionPolicy Bypass -File .\scripts\tools\trade.ps1 BUY MARKET
```

Notes:
- All safety stays: risk-gate + adaptive sizing + file logs with absolute paths/URIs.
- No core files touched.
