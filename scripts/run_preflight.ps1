<# Wrapper to run preflight checks.
Usage:
  powershell -ExecutionPolicy Bypass -File .\scripts\run_preflight.ps1
#>
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)  # scripts/

# choose python
$venvPython = Join-Path "..\.venv\Scripts" "python.exe"
if (Test-Path $venvPython) { $Python = $venvPython } else { $Python = "python" }

& $Python ".\preflight_live.py"
exit $LASTEXITCODE
