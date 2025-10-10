
# Release Readiness Report

**Status:** unit/contract/integration-lite ✅ — 29/29 green (as of last run).  
**Estimated readiness for "ideal & release": ~75%**

## Why not 100% yet
1. **Live exchange integration hardening:** timeouts, retries, rate-limit handling, WS reconnects, idempotency on order placement.
2. **State resilience:** safe resume after restart (open positions sync, pending orders reconciliation).
3. **Risk enforcement in live path:** ensure `can_open_new_trade` (and other guards) are enforced before *every* live order; add audit log.
4. **Backtest ↔ live parity:** verify fees/slippage/lot size/rounding rules match exchange filters; unit tests for filters; a small parity check.
5. **Telemetry/alerts:** error alerts (TG/Slack), log rotation, structured logs (JSON) for later analytics.
6. **Dependency hygiene:** pin versions; address `websockets.legacy` deprecation by either pin or upgrade path; Python 3.13 compat check.
7. **Ops readiness:** `.env.example`, secrets loading, one-command run scripts (dry-run/testnet/prod).

## Suggested next steps (in order)
1) **Trading client adapter (offline-safe):** introduce a `TradingClient` facade with default timeouts and no network on import. Add contract tests to ensure constructor is offline-safe.  
2) **Exchange filters & rounding:** add helpers for tick/step/lot size; tests with sample filters JSON.  
3) **Risk guard in live path:** a thin decorator/check to call `can_open_new_trade` before sending orders; contract test that fails if not called (via monkeypatch).  
4) **State snapshot/resume:** persist open-positions snapshot; add a resume test (offline) validating merge logic.  
5) **Alerts & logs:** add file rotation and a minimal Telegram/Slack notifier (disabled by default), with tests that assert formatting (no network).  
6) **Pin/upgrade deps:** pin `websockets<14` (or adapt to 14+), `urllib3`, `requests`, `python-binance`/client of choice; freeze `requirements.txt` and add a constraints file.  
7) **(Optional) CI & coverage:** enforce `pytest -q` and a modest coverage gate (e.g., 50–60%) on PR.

## Acceptance criteria for "release-ready"
- Dry-run & testnet runs are deterministic, no unhandled exceptions for 24h.
- Live risk checks always executed (audited).
- Reconnect & retry paths covered by tests (simulated).  
- Version pins; reproducible install on Windows (PowerShell scripts).

