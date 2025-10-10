# Logging Pack v1 (non-breaking)
Adds safe JSON logging for diagnostics (no code changes needed).

Files:
- `utils/logrotate.py`                → Rotate logs by age/size (used by safe_ops rotate-logs)
- `scripts/diagnostics/log_preflight.py` → Runs preflight checks and writes JSON into `logs/preflight/YYYYMMDD/*.json`
- `scripts/diagnostics/log_sizer.py`     → Computes qty+leverage and writes JSON into `logs/sizer/YYYYMMDD/*.json`

Examples:
```powershell
# 1) Preflight log
powershell -ExecutionPolicy Bypass -File .\scripts\tools\safe_ops.ps1 preflight
.\.venv\Scripts\python.exe .\scripts\diagnostics\log_preflight.py

# 2) Sizer log (set your balance and params)
$env:WALLET_USDT=103; $env:SYMBOL="BTCUSDT"; $env:RISK_MARGIN_FRACTION=0.2; $env:PREFERRED_MAX_LEVERAGE=10
.\.venv\Scripts\python.exe .\scripts\diagnostics\log_sizer.py

# 3) Rotate logs
powershell -ExecutionPolicy Bypass -File .\scripts\tools\safe_ops.ps1 rotate-logs logs 100 14
```
