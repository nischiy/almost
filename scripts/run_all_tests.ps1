<# 
Run all tests with pytest (Windows-safe).
- No PYTEST_ADDOPTS used (avoid env side-effects).
- Optional --timeout only if pytest-timeout is installed.
- Writes reports to logs\reports.
#>

$ErrorActionPreference = "Stop"

# Move to project root
Set-Location (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))

# Prefer venv python
$venvPython = Join-Path ".\.venv\Scripts" "python.exe"
if (Test-Path $venvPython) { $Python = $venvPython } else { $Python = "python" }

# Ensure pytest
$have_pytest = $false
try { & $Python -c "import pytest" 2>$null; $have_pytest = $true } catch { }
if (-not $have_pytest) {
  & $Python -m pip install -q pytest pytest-xdist 2>$null | Out-Null
}

# Detect pytest-timeout quietly
& $Python -c "import importlib.util, sys; sys.exit(0) if importlib.util.find_spec('pytest_timeout') else sys.exit(1)" 2>$null
$have_timeout = ($LASTEXITCODE -eq 0)

# Prepare reports
if (!(Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }
if (!(Test-Path "logs\reports")) { New-Item -ItemType Directory -Path "logs\reports" | Out-Null }
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$reportJUnit = "logs\reports\pytest_${ts}.junit.xml"
$reportTxt   = "logs\reports\pytest_${ts}.txt"

# Avoid auto-loaded 3rd-party plugins
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTEST_ADDOPTS = ""

# Build argument array
$pytestArgs = @("--maxfail=1", "-ra", "--durations=20", "--junitxml=$reportJUnit", "-q", "tests")
if ($have_timeout) { $pytestArgs += @("--timeout=60") }

Write-Host "=== Running full test suite ==="
Write-Host "Command: $Python -m pytest $($pytestArgs -join ' ')"

# Execute and tee output
& $Python -m pytest @pytestArgs *>&1 | Tee-Object -FilePath $reportTxt

$code = $LASTEXITCODE
if ($code -eq 0) {
  Write-Host ""
  Write-Host "ALL TESTS PASSED ✅" -ForegroundColor Green
  Write-Host "Report:"
  Write-Host " - $reportTxt"
  Write-Host " - $reportJUnit"
  exit 0
} else {
  Write-Host ""
  Write-Host "TESTS FAILED ❌ (exit=$code)" -ForegroundColor Red
  Write-Host "See reports:"
  Write-Host " - $reportTxt"
  Write-Host " - $reportJUnit"
  exit $code
}
