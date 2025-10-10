<#
  Install project dependencies into the project's virtual environment.
  Usage (from project root):
    powershell -ExecutionPolicy Bypass -File .\scripts\install_deps.ps1
#>
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path   # scripts folder
$root = Resolve-Path (Join-Path $here "..")

# Prefer venv python under project root
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
if (Test-Path $venvPy) { $Python = $venvPy } else { $Python = "python" }

Write-Host ">>> Project root:" $root
Write-Host ">>> Using Python:" $Python

& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$req = Join-Path $root "requirements.txt"
if (Test-Path $req) {
    Write-Host ">>> Installing from" $req
    & $Python -m pip install -r $req
    exit $LASTEXITCODE
} else {
    Write-Warning "requirements.txt not found at project root: $req"
    Write-Host ">>> Installing critical dependency directly: python-binance>=1.0.19"
    & $Python -m pip install "python-binance>=1.0.19"
    exit $LASTEXITCODE
}
