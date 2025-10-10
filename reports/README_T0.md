# T0 Baseline Toolkit — How to use

This kit computes your 14‑day baseline metrics and writes two artifacts:
- `logs/snapshots/T0_baseline.json`
- `reports/T0_metrics.md`

## What it measures
- **Win‑rate** (% of winning trades)
- **Profit Factor** (Sum wins / Abs sum losses)
- **MAR (short-window)** = NetPnL / MaxDrawdown (not annualized)
- **Max drawdown** (by equity curve over the window)
- **Average R** (only if your CSV has a column `R`)
- **Average slippage** (only if your CSV has `slippage`)
- **% days without trades**

## Expected input
A **per‑trade CSV** under `logs/` with columns:
```
entry_time, exit_time, entry_price, exit_price, qty, side, pnl[, fees, r, slippage, symbol]
```
The toolkit will search common locations like:
- `logs/trades/*.csv`
- `logs/trades.csv`
- `logs/decisions/*trades*.csv`
- (last resort) any `logs/**/*.csv`

> If only decision/fill logs exist (no per-trade CSV), first export trades from your project into a per-trade CSV, then re-run.

## Quick start (Windows PowerShell)
1. **Unzip** the kit **into your project root** (same level as `logs/`, `app/`, `core/`).
2. (Optional) **Activate venv**: `.\.venv\Scripts\Activate.ps1`
3. Run:
```
powershell -ExecutionPolicy Bypass -File .\scripts\make_t0_baseline.ps1
```
4. Open:
   - `logs/snapshots/T0_baseline.json`
   - `reports/T0_metrics.md`

## Exit codes & Troubleshooting
- **2** — No CSV candidates found under `logs/`.
- **3** — Found CSVs, but none had the required per-trade columns.
- **4** — Parsed CSV OK, but **no trades closed in last 14 days**.

In each case, the error message will tell you what to fix precisely.

## Why this step matters
Step **0 (T‑0h)** fixes a **ground truth** baseline so you can compare all further changes (risk/sizing/filters) against the same 14‑day window. That protects you from "it seems better" illusions and keeps releases honest.
