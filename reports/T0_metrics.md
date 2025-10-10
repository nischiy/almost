# T0 Baseline Metrics (last 14 days)

- Generated (UTC): 2025-09-25T03:11:46Z
- Source file: `trades_exported.csv`
- Window: 14 days

| Metric | Value |
|---|---|
| Trades | 1 |
| Wins | 1 |
| Losses | 0 |
| Win rate | 100.0 % |
| Profit Factor | None |
| Net PnL | 0.04 |
| Max Drawdown | 0.0 |
| MAR ratio | None |
| Average R | None |
| Average slippage | None |
| % days without trades | 0.0 % |

## Notes & Assumptions
- Metrics are computed from **closed trades** within the last 14 days.
- **Profit Factor** = Sum(positive PnL) / Abs(Sum(negative PnL)).
- **MAR (short-window)** = NetPnL / MaxDrawdown (not annualized).
- **Average R** is reported only if an `R` column exists in the trade CSV.
- **Average slippage** reported only if `slippage` column exists.