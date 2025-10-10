<#
  Regenerate a pinned lock file from the active .venv

  Usage (from project root):
    powershell -ExecutionPolicy Bypass -File .\scripts\pin_requirements.ps1

  Output:
    - requirements.lock.txt  (exact versions from pip freeze)
#>
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $here "..")
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
if (Test-Path $venvPy) { $Python = $venvPy } else { $Python = "python" }

Write-Host ">>> Using Python:" $Python
$lock = Join-Path $root "requirements.lock.txt"
& $Python -m pip freeze | Out-File -Encoding ASCII $lock
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host ">>> Wrote" $lock
