# scripts/kill_stuck_pytest.ps1
Get-Process python, pytest -ErrorAction SilentlyContinue | Where-Object { $_.CPU -gt 180 } | Stop-Process -Force
