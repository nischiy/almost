# Order Dry-Run Pack v1 (non-breaking)
Builds a non-sending futures order payload using position_sizer + risk_guard, writes JSON to logs/orders/YYYYMMDD/*.

Run examples:
```powershell
# MARKET BUY dry-run
$env:WALLET_USDT=103; $env:SYMBOL="BTCUSDT"; $env:RISK_MARGIN_FRACTION=0.2; $env:PREFERRED_MAX_LEVERAGE=10
$env:SIDE="BUY"; $env:TYPE="MARKET"
.\.venv\Scripts\python.exe .\scripts\diagnostics\order_dry_run.py

# LIMIT SELL dry-run @ price
$env:SIDE="SELL"; $env:TYPE="LIMIT"; $env:PRICE=120000
.\.venv\Scripts\python.exe .\scripts\diagnostics\order_dry_run.py
```
