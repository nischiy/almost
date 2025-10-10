<#
  Quick fix installer for python-binance when requirements.txt is not yet updated.
  Usage:
    powershell -ExecutionPolicy Bypass -File .\scripts\install_python_binance.ps1
#>
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $here "..")
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
if (Test-Path $venvPy) { $Python = $venvPy } else { $Python = "python" }
Write-Host ">>> Using Python:" $Python
& $Python -m pip install "python-binance>=1.0.19"
exit $LASTEXITCODE
