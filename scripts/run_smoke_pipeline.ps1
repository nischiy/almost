Param(
    [switch]$SkipTests = $false
)
Write-Host "=== Smoke Pipeline ==="
# 1) Preflight
.\scripts\preflight.ps1 -Strict
if ($LASTEXITCODE -ne 0) { 
  Write-Host "Preflight failed." -ForegroundColor Red
  exit 1 
}
# 2) Tests (optional)
if (-not $SkipTests) {
  pytest -q -vv
  if ($LASTEXITCODE -ne 0) { 
    Write-Host "Tests failed." -ForegroundColor Red
    exit 1 
  }
}
# 3) Offline backtest on synthetic data
python tools\smoke_pipeline.py
$code = $LASTEXITCODE
if (Test-Path logs\smoke_report.json) {
  Write-Host "Report: logs\smoke_report.json"
} else {
  Write-Host "Report not found (tools\smoke_pipeline.py should create logs\smoke_report.json)"
}
exit $code
