param(
  [string]$ProjectRoot = ".",
  [int]$Days = 180
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host "=== Install deps + Pull trades + Baseline ==="
Write-Host "ProjectRoot = $root"
Write-Host ("Days window = {0}" -f $Days)

# venv python
$py = Join-Path -Path $root -ChildPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) {
  $py = "python"
}

# 1) Upgrade pip and install deps
& $py -m pip install --upgrade pip
& $py -m pip install --upgrade "python-binance>=1.0.19"

# 2) Pull trades
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\pull_trades_from_binance.ps1") -ProjectRoot $root -Days $Days

# 3) Baseline
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\make_t0_baseline.ps1") -ProjectRoot $root
