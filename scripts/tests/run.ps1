# scripts\run_tests.ps1  (fixed quotes, no emoji)
param(
  [switch]$VerboseMode
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host ">>> Running unit tests (unittest discover)..." -ForegroundColor Cyan

# Ensure we run from project root (parent of scripts)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir\..

# Activate venv if present
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
  . .\.venv\Scripts\Activate.ps1
}

# Suppress noisy warnings to keep output clean
$env:PYTHONWARNINGS = "ignore"

# Run tests
python -m unittest discover -s tests -p "test_*.py"
$code = $LASTEXITCODE

if ($code -ne 0) {
  Write-Host ("Tests failed with exit code {0}" -f $code) -ForegroundColor Red
  exit $code
} else {
  Write-Host "All tests passed" -ForegroundColor Green
  exit 0
}
