param(
  [string]$ProjectRoot = "."
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path

Write-Host "=== T0 Baseline: compute 14-day metrics ==="
Write-Host "ProjectRoot = $root"

# Try to locate a venv Python if present
$pyCandidates = @(
  (Join-Path -Path $root -ChildPath ".venv\Scripts\python.exe"),
  "python",
  "py -3"
)

$pythonExe = $null
foreach ($c in $pyCandidates) {
  try {
    & $c --version | Out-Null
    $pythonExe = $c
    break
  } catch {}
}

if (-not $pythonExe) {
  throw "Python interpreter not found. Please activate your venv or install Python."
}

$scriptPath = Join-Path -Path $root -ChildPath "tools\metrics\compute_baseline.py"
if (-not (Test-Path -LiteralPath $scriptPath)) {
  throw "Missing tools\metrics\compute_baseline.py. Make sure you've unzipped the kit at project root."
}

# Run the baseline computation
& $pythonExe $scriptPath --project-root $root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== Done. See outputs in logs\snapshots\T0_baseline.json and reports\T0_metrics.md ==="
