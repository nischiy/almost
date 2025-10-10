param(
  [string]$ProjectRoot = "."
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path

Write-Host "=== Export per-trade CSV from logs ==="
Write-Host "ProjectRoot = $root"

$pyCandidates = @(
  (Join-Path -Path $root -ChildPath ".venv\Scripts\python.exe"),
  "python",
  "py -3"
)

$pythonExe = $null
foreach ($c in $pyCandidates) {
  try { & $c --version | Out-Null; $pythonExe = $c; break } catch {}
}

if (-not $pythonExe) { throw "Python interpreter not found. Activate venv or install Python." }

$scriptPath = Join-Path -Path $root -ChildPath "tools\trades\export_trades.py"
if (-not (Test-Path -LiteralPath $scriptPath)) {
  throw "Missing tools\trades\export_trades.py. Unzip the kit at project root."
}

& $pythonExe $scriptPath --project-root $root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== Done. See logs\trades\trades_exported.csv ==="
