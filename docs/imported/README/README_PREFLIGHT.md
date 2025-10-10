# Pre-flight (LIVE) checks

Run from project root:

```powershell
# Optionally activate venv
# .\.venv\Scripts\Activate.ps1

# Run preflight
powershell -ExecutionPolicy Bypass -File .\scripts\run_preflight.ps1
```

What it does:
- Validates env flags for LIVE: `PAPER_TRADING=0`, `TRADE_ENABLED=1`, `BINANCE_TESTNET=false`
- Public API ping (`/fapi/v1/ping`), server time drift
- `exchangeInfo` for your `SYMBOL` (LOT_SIZE, PRICE_FILTER, MIN_NOTIONAL)
- Optional private balance check if API keys present and LIVE mode (non-fatal on failure)

Exit code `0` → OK; `1` → issues found. Reports are printed in console.
