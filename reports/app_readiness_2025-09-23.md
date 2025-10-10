# App Folder Readiness — 2025-09-23

**Verdict:** Not 100% production-ready. Functional for paper mode. **Estimated readiness: 72%** for full release.

## Summary
- Core loop runs end-to-end (data → signal → risk → execution → telemetry).
- Market data works via Binance public REST fallback (no API key needed); suitable for paper & backfill, not ideal for production due to rate limits/retries.
- Signals generate decisions and now include **SL/TP** (ATR-based).
- Risk gate exists but is minimal; no position sizing, daily loss limits, or stateful exposure guard.
- Execution is non-destructive by default (paper/logging). Real order routing (Spot/Futures) is not wired here yet.
- Telemetry health is fixed and writes JSONL + console; `snapshot/decision` fallbacks exist, but service methods are placeholders.

## Component Checklist
| Component | Status | Notes | Ready % |
|---|---|---|---:|
| `app/run.py` (orchestrator) | ✅ Pass | Robust wiring + diagnostics; handles loop and once modes | 90% |
| `services/market_data.py` | ⚠️ Partial | Public REST fallback only; add API-keyed provider, retries, rate-limit backoff | 70% |
| `services/signal.py` | ✅ Pass | EMA/RSI/ATR + SL/TP; params via `params` dict; consider config-driven tuning | 85% |
| `services/risk.py` | ⚠️ Minimal | Only basic gate; no position sizing, max exposure, daily DD guard, SL/TP validation | 55% |
| `services/execution.py` | ⚠️ Paper | Logs intent; no live order placement / OCO / idempotency | 50% |
| `services/telemetry.py` | ⚠️ Basic | Health logs OK; snapshot/decision methods are stubs relying on fallbacks | 65% |
| Entrypoint (`app/entrypoint.py`) | ✅ Pass | No premature gating; respects args & overrides | 90% |
| Update log (`scripts.update_log`) | ✅ Pass | CLI works in PowerShell (use backtick line breaks) | 95% |

**Overall readiness (full release): ~72%**

## Blocking gaps for “Full Release”
1. **Execution (Live Trading)**
   - Implement exchange client (Spot/Futures) and real order flow (market/limit + OCO for SL/TP).
   - Add idempotency keys and retry policies; confirm symbol precision/lot filters.
2. **Risk Management**
   - Position sizing (e.g., ATR-/balance-based), per-trade and daily loss limits, max concurrent exposure.
   - Validate SL/TP distances vs. exchange filters.
3. **Market Data Reliability**
   - Add API-keyed data source or websocket stream; implement retry with exponential backoff and http error handling.
4. **Telemetry & Observability**
   - Implement `snapshot()` and `decision()` writers (CSV/Parquet/DB), plus alerting (Telegram/Slack) for errors and fills.
5. **Config & Parameters**
   - Centralize params in `.env`/config (ema/rsi/atr/sl_atr/tp_atr/qty) to avoid code edits.
6. **Testing & Safety**
   - Smoke tests for each service; dry run mode; guards to prevent live trading unless explicitly enabled.

## Quick Verification Steps (you can run now)
1. **Paper cycle once** (already passes):
   ```
   python -m app.entrypoint --once --paper --enabled --symbol BTCUSDT --strategy ema_rsi_atr --sleep 2
   ```
2. **Run loop** for a few cycles and watch decisions:
   ```
   python -m app.entrypoint --loop --paper --enabled --symbol BTCUSDT --strategy ema_rsi_atr --sleep 5
   ```
3. **Check logs**:
   - Health: `logs/health/<YYYY-MM-DD>/health.jsonl`
   - Decisions: `logs/decisions/<YYYY-MM-DD>.csv`
   - Updates: `logs/updates/CHANGELOG.md`

## Suggested Minimal Next Patches (surgical)
- `execution.py`: add paper OCO simulation (SL/TP state machine) to verify logic before live.
- `risk.py`: add position sizing (ATR × risk%), daily drawdown guard, and SL/TP distance checks.
- `market_data.py`: add simple retry/backoff and optional API-keyed provider switch.

---

*This report is generated to keep scope tight and changes surgical. Once Execution/Risk are upgraded, readiness should move >90%.*
