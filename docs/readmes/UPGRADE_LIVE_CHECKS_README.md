# Live Checks Addon

This bundle adds two **safe** live checks for your project:

1) `scripts/live/check_account.ps1` — signed `/api/v3/account` call to verify API key/secret.
2) `scripts/live/read_ticker.ps1` — unsigned bookTicker fetch for a symbol (market data only).

## How to install
Unzip the archive into your repo root so the paths look like:
```
scripts/live/check_account.ps1
scripts/live/read_ticker.ps1
tools/live/check_account.py
```

## Usage

### 1) Market data (no keys needed)
```powershell
.\scripts\live
ead_ticker.ps1           # uses SYMBOL from .env or BTCUSDT
.\scripts\live
ead_ticker.ps1 -Symbol ETHUSDT
```

### 2) Account check (needs keys)
Ensure `.env` contains:
```
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
BINANCE_TESTNET=true   # set true to hit testnet, false for production
```
Then run:
```powershell
.\scripts\live\check_account.ps1
```

**Exit codes**: 0 = OK, 1 = API error, 2 = missing keys, 3 = network/exception.
