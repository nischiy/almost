# Safe Update Pack v3 (non-breaking)
Adds/updates diagnostics and sizing helpers. No core code modified.
- scripts/diagnostics/preflight_v2.py
- scripts/diagnostics/size_advisor.py
- scripts/diagnostics/leverage_sizer_standalone.py
- scripts/tools/safe_ops.ps1 (compat, no stray chars)
- utils/position_sizer.py (fixed leverage calc)

Quick check:
  powershell -ExecutionPolicy Bypass -File .\scripts\tools\safe_ops.ps1 preflight
  $env:WALLET_USDT=103; $env:SYMBOL='BTCUSDT'; $env:RISK_MARGIN_FRACTION=0.2; $env:PREFERRED_MAX_LEVERAGE=10
  .\.venv\Scripts\python.exe .\scripts\diagnostics\leverage_sizer_standalone.py
