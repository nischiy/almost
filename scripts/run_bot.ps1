param(
  [string]$ProjectRoot = "."
)
Set-StrictMode -Off
$ErrorActionPreference = "Stop"

Push-Location $ProjectRoot
try {
  if (-not (Test-Path ".venv")) {
    python -m venv .venv
  }
  .\.venv\Scripts\Activate.ps1
  $env:PYTHONPATH = (Get-Location).Path
  if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path logs | Out-Null }
  Write-Host "Starting bot (module app.run)..." -ForegroundColor Green
  python -m app.run
} finally {
  Pop-Location
}
