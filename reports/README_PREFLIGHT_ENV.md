# ENV & Binance Preflight — what this does

- Validates your `.env` keys and types.
- Resolves whether TESTNET is enabled (`BINANCE_TESTNET`).
- If API keys are present, pings UM Futures and checks basic permissions.

## Run
```
powershell -ExecutionPolicy Bypass -File .\scripts\check_env_and_binance.ps1
```
Exit codes:
- **0**: OK
- **2**: `.env` missing or required fields absent
- **3**: `python-binance` import error
- **4**: API/permission error

Use this before pulling trades or starting live to avoid silent misconfig.
