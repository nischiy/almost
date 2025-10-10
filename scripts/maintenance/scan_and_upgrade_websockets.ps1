param(
  [switch]$Apply = $false,
  [string]$ProjectRoot = ".",
  [switch]$VerboseLog = $true
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$m) { if ($VerboseLog) { Write-Host $m } }

$py = Join-Path $ProjectRoot "scripts/maintenance/upgrade_websockets_imports.py"
if (!(Test-Path -LiteralPath $py)) {
  throw "Missing scripts/maintenance/upgrade_websockets_imports.py"
}

Write-Info "[SCAN] Searching and upgrading websockets imports…"
$applyFlag = $Apply ? "--apply" : ""
$cmd = "python `"$py`" --project-root `"$ProjectRoot`" $applyFlag"
Write-Host "[CMD] $cmd"
& python $py --project-root $ProjectRoot @($Apply ? "--apply" : $null)

try {
  $ver = python - << 'PY'
import importlib, sys
try:
    ws = importlib.import_module("websockets")
    print(ws.__version__)
except Exception as e:
    print("not-installed")
PY
  Write-Info "[WEBSOCKETS] $ver"
} catch { Write-Info "[WEBSOCKETS] not-installed" }
