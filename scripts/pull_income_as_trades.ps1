param(
  [string]$ProjectRoot = ".",
  [int]$Days = 365
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path

Write-Host "=== Pull UM Futures Income as Trades (fallback) ==="
Write-Host "ProjectRoot = $root"
Write-Host ("Days window = {0}" -f $Days)

$py = Join-Path -Path $root -ChildPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) { $py = "python" }

# Ensure dependency
& $py -m pip install --upgrade "python-binance>=1.0.19"

$scriptPath = Join-Path -Path $root -ChildPath "tools\trades\pull_income_as_trades.py"
& $py $scriptPath --project-root $root --days $Days
exit $LASTEXITCODE
