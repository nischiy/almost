param(
  [string]$ProjectRoot = ".",
  [string]$Version = "1.0.29"
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$py = Join-Path -Path $root -ChildPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) { throw ".venv python not found at $py" }

Write-Host "=== Hard-fix python-binance in venv ==="
& $py -m pip uninstall -y binance 2>$null | Out-Null
& $py -m pip uninstall -y python-binance 2>$null | Out-Null
& $py -m pip install --upgrade ("python-binance==" + $Version)

# Verify import via temp script
$tmp = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "verify_um_{0}.py" -f ([guid]::NewGuid().ToString("N")))
@'
import importlib, sys
m = importlib.import_module("binance.um_futures")
print("binance.um_futures path:", m.__file__)
'@ | Out-File -LiteralPath $tmp -Encoding UTF8

& $py $tmp
Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
