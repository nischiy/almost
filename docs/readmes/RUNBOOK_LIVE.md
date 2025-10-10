# Runbook: Switching to LIVE

1. Copy `.env.example` → `.env`, set:
   - `TRADE_ENABLED=1`
   - `DRY_RUN=0`
   - `PRE_FLIGHT_SKIP_API=0`
   - Add `API_KEY`, `API_SECRET`
2. Verify risk:
   - `RISK_MAX_DD_PCT_DAY`, `RISK_MAX_LOСС_USD_DAY`, `KILL_SWITCH_ENABLED=1`
3. Preflight:
   ```bash
   python scripts/preflight_all.py
   ```
4. Final unit/integration tests:
   ```bash
   pytest -q
   ```
5. Start:
   ```bash
   python main.py
   ```
6. Monitor `logs/health/*` and `logs/decisions/*` during first 24h.
