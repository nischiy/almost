# Position Manager Pack v1 (add-only)
Purpose: add **exit management** (SL/TP) and optional **live balance** fetch.

Files:
- utils/balance_provider.py   → live wallet (if LIVE_BALANCE=1) or env WALLET_USDT
- utils/exit_adapter.py       → build/send reduce-only full-close exits (STOP_MARKET / TAKE_PROFIT_MARKET)
- scripts/diagnostics/set_tp_sl_cli.py → CLI to preview/send exits; writes logs with absolute paths.

Preview SL/TP (no sending):
```powershell
$env:SYMBOL="BTCUSDT"; $env:SIDE="BUY"   # entry side; for long exits will be SELL closePosition
$env:SL_PRICE=110000; $env:TP_PRICE=120000
.\.venv\Scripts\python.exe .\scripts\diagnostics\set_tp_sl_cli.py
```

Send SL/TP (testnet first!):
```powershell
$env:BINANCE_FAPI_BASE="https://testnet.binancefuture.com"
$env:API_KEY="..."; $env:API_SECRET="..."; $env:DRY_RUN_ONLY=0
$env:SYMBOL="BTCUSDT"; $env:SIDE="BUY"; $env:SL_PRICE=110000; $env:TP_PRICE=120000; $env:SEND_EXITS=1
.\.venv\Scripts\python.exe .\scripts\diagnostics\set_tp_sl_cli.py
```

Live balance (optional):
```powershell
$env:LIVE_BALANCE=1
# Requires API keys; falls back to WALLET_USDT if request fails
```
