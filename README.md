# Trading Bot Strategies

## Strategy selection
Set `STRATEGY_NAME` to one of the supported rule-based strategies:

- `ema_rsi_atr` (default)
- `breakout_donchian_atr`
- `mean_reversion_bb_rsi`
- `trend_pullback_ema_atr`

## Strategy summaries
### `ema_rsi_atr`
Trend-following EMA crossover with RSI confirmation and ATR-based SL/TP. It looks for EMA fast/slow alignment with RSI overbought/oversold levels and suggests ATR-based risk targets.

### `breakout_donchian_atr`
Breakout strategy using Donchian (20) highs/lows with ATR context and a volume ratio filter. It triggers on price breaks with sufficient volume, optionally filtered by EMA200 trend.

### `mean_reversion_bb_rsi`
Mean-reversion strategy using Bollinger Bands (20, 2) and RSI (14). It looks for price extremes outside the bands plus RSI overbought/oversold, optionally filtered by EMA200 trend direction.

### `trend_pullback_ema_atr`
Trend pullback strategy based on EMA50/EMA200 with ATR-scaled pullbacks. It waits for pullbacks near EMA50 within a multiple of ATR and a rejection back in the trend direction.
