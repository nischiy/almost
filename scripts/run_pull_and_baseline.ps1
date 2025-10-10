param(
  [string]$ProjectRoot = ".",
  [int]$Days = 180
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host "=== RUN: deps -> preflight -> pull -> baseline (venv forced) ==="
Write-Host "ProjectRoot = $root"
Write-Host ("Days window = {0}" -f $Days)

$py = Join-Path -Path $root -ChildPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) {
  throw ".venv Python not found at $py. Activate/create venv named .venv in project root."
}

# deps
& $py -m pip install --upgrade pip
& $py -m pip install --upgrade "python-binance>=1.0.19"

# preflight
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\check_env_and_binance.ps1") -ProjectRoot $root

# pull
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\pull_trades_from_binance.ps1") -ProjectRoot $root -Days $Days

# baseline
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\make_t0_baseline.ps1") -ProjectRoot $root
