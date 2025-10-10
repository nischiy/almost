# Release Go-Live Pack v1 (add-only)
Two options to go LIVE on mainnet quickly.

## A) One-command live trade (+optional SL/TP)
Prereqs:
- Set **API_KEY**, **API_SECRET**
- Set **DRY_RUN_ONLY=0**
- Ensure: `BINANCE_TESTNET=false`, `PAPER_TRADING=0`, `TRADE_ENABLED=1`

Example:
```powershell
# core
$env:TRADE_ENABLED=1; $env:PAPER_TRADING=0; $env:DRY_RUN_ONLY=0
$env:SYMBOL="BTCUSDT"; $env:WALLET_USDT=103
$env:RISK_MARGIN_FRACTION=0.2; $env:PREFERRED_MAX_LEVERAGE=10

# LIVE entry + exits
powershell -ExecutionPolicy Bypass -File .\scripts\tools\go_live.ps1 BUY MARKET -SL 110000 -TP 120000
```

## B) Minimal live loop (opt-in)
```powershell
$env:TRADE_ENABLED=1; $env:PAPER_TRADING=0; $env:DRY_RUN_ONLY=0
$env:WALLET_USDT=103; $env:SYMBOL="BTCUSDT"
$env:LOOP_SIDE="BUY"; $env:LOOP_TYPE="MARKET"
$env:LOOP_SL=110000; $env:LOOP_TP=120000
$env:LOOP_SLEEP_S=10
.\.venv\Scripts\python.exe .\scripts\run\loop_live_safe.py
```
This loop is conservative and uses our full safety stack. Prefer integrating `utils.order_service.place(...)` into your own strategy loop for production.
