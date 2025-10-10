# Fixpack J — Export StrategyEMA_RSI_ATR from core.strategy (2025-09-22)

Some projects define the EMA/RSI/ATR strategy in `core/strategies/ema_rsi_atr.py` but tests import it from `core.strategy`.
This patch appends a compatibility re-export to `core/strategy.py` if the name is missing.

## Apply
1) Unzip over your project.
2) Run:
   ```powershell
   python .\scripts\patch_strategy_export.py .
   ```
3) Re-run the release check:
   ```powershell
   .\scripts\release_check.ps1 -ProjectRoot .
   ```

A backup of `core/strategy.py` is saved as `core/strategy.py.bak_strategy_export`.
