param(
  [string]$ProjectRoot = "."
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host "=== ENV & Binance UM Futures Preflight (venv forced) ==="
Write-Host "ProjectRoot = $root"

$py = Join-Path -Path $root -ChildPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) {
  throw ".venv Python not found at $py. Activate/create venv named .venv in project root."
}

# deps for preflight
& $py -m pip install --upgrade "python-binance>=1.0.19"

$scriptPath = Join-Path -Path $root -ChildPath "tools\preflight\check_env_and_binance.py"
& $py $scriptPath --project-root $root
exit $LASTEXITCODE
