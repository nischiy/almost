# Release Checklist (GO/NO-GO)

## Preflight
- [ ] `.env` exists (copied from `.env.example`) and has real API keys when `TRADE_ENABLED=1`
- [ ] `BINANCE_TESTNET` set correctly (true for sandbox, false for mainnet)
- [ ] `PAPER_TRADING` and `DRY_RUN` reflect desired mode
- [ ] `PARAMS_PATH` points to a valid JSON with tuned params
- [ ] Run: `python scripts/preflight_all.py` → All checks GREEN

## Risk / Trading Limits
- [ ] Daily max drawdown and loss limits configured (`RISK_MAX_DD_PCT_DAY`, `RISK_MAX_LOSS_USD_DAY`)
- [ ] Kill-switch enabled and verified
- [ ] Trade rate limit tuned (`RISK_MAX_TRADES_DAY`)

## Telemetry / Logs
- [ ] Snapshot/Decision/Health logs writing to `./logs/`
- [ ] App version and params logged in snapshots

## Tests / QA
- [ ] `pytest -q` passes locally
- [ ] `tests/test_live_exec_e2e.py` passes (mocks cover idempotency and filters)

## Run
- [ ] Dry-run sane (PnL not exploding due to fees/slippage)
- [ ] Live toggle reviewed by human
