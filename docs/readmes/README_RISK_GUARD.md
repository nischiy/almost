# Risk Guard Pack v1 (non-breaking)
Offline guard to gate trading by simple limits (daily trades, loss streak, daily drawdown).
Files:
- utils/risk_guard.py
- scripts/diagnostics/risk_guard_check.py

Run demo:
  $env:RG_MAX_TRADES_PER_DAY=20; $env:RG_MAX_LOSS_STREAK=5; $env:RG_MAX_DD_USDT=50
  $env:RG_TRADES_TODAY=3; $env:RG_LOSS_STREAK=0; $env:RG_PNL_TODAY=-12.5
  .\.venv\Scripts\python.exe .\scripts\diagnostics\risk_guard_check.py
