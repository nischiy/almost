param(
  [string]$Symbol = "BTCUSDT",
  [string]$Interval = "1m",
  [int]$Months = 1,
  [int]$Leverage = 5,
  [int]$PositionUSD = 50
)

$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"

Write-Host ">>> 1) Self-check"
& $py tests\self_check.py

Write-Host ">>> 2) Smoke backtest (pre-tune)"
& $py scripts\backtest.py --symbol $Symbol --interval $Interval --months $Months `
  --leverage $Leverage --position-usd $PositionUSD

Write-Host ">>> 3) Tune params (light grid)"
& $py scripts\tune_simple.py --symbol $Symbol --interval $Interval --months $Months --out models/ema_rsi_atr/best_params.json

Write-Host ">>> 4) Freeze best params snapshot"
& $py scripts\save_current_params.py --name ema_rsi_atr

Write-Host ">>> 5) Backtest with tuned params"
& $py scripts\backtest.py --symbol $Symbol --interval $Interval --months $Months `
  --leverage $Leverage --position-usd $PositionUSD --params models/ema_rsi_atr\best_params.json

Write-Host ">>> Done. Check logs/ and models/ for results."
