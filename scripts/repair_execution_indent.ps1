# Convenience wrapper
$ErrorActionPreference = "Stop"
Write-Host "Repairing app/services/execution.py ..." -ForegroundColor Cyan
python .\scripts\repair_execution_indent.py
