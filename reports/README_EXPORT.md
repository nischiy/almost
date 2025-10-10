# Trade Export Kit — make per‑trade CSV from your logs

This tool reconstructs per‑trade round trips so that the T0 Baseline step can run.

## What it does
- Searches your logs for execution fills or decision events.
- Rebuilds **round trips** (ENTRY → EXIT) per symbol using position changes.
- Writes `logs/trades/trades_exported.csv` with the required columns.

## Inputs it can read
Priority order:
1. `logs/orders/*.jsonl` — one JSON object per line (fills/execution reports).
2. `logs/orders/fills*.csv` — comma files with fills.
3. `logs/decisions/*.csv` — if no fills available (best‑effort pairing of ENTRY/EXIT).

## Output columns (per‑trade):
```
entry_time, exit_time, entry_price, exit_price, qty, side, pnl, fees, r, slippage, symbol
```

- `pnl`: uses `realizedPnl` from fills when present; otherwise approximates:
  - LONG: `(exit_price - entry_price) * qty`
  - SHORT: `(entry_price - exit_price) * qty`
- `fees`: sum of `commission`/`fee` if available.
- `r`, `slippage`: left blank (you can enrich later).

## How to run (Windows PowerShell)
1. Unzip this kit to your **project root**.
2. (Optional) Activate venv: `.\.venv\Scripts\Activate.ps1`
3. Run:
```
powershell -ExecutionPolicy Bypass -File .\scripts\export_trades_ps1.ps1
```
4. Check `logs/trades/trades_exported.csv`.
5. Now run the T0 baseline:
```
powershell -ExecutionPolicy Bypass -File .\scripts\make_t0_baseline.ps1
```

## Exit codes
- **2** — no candidate logs found.
- **3** — failed to reconstruct trades from available logs.

If that happens, send me a snippet of one of your log files (just headers + 5–10 rows), and I’ll add an adapter.
