param(
  [string]$ProjectRoot = ".",
  [int]$Days = 180
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host "=== Pull Binance UM Futures trades (venv forced) ==="
Write-Host "ProjectRoot = $root"
Write-Host ("Days window = {0}" -f $Days)

$py = Join-Path -Path $root -ChildPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) {
  throw ".venv Python not found at $py. Activate/create venv named .venv in project root."
}

# ensure deps in THIS interpreter
& $py -m pip install --upgrade "python-binance>=1.0.19"

$scriptPath = Join-Path -Path $root -ChildPath "tools\trades\pull_from_binance.py"
& $py $scriptPath --project-root $root --days $Days
exit $LASTEXITCODE
