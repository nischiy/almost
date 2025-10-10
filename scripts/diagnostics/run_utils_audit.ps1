param([string]$ProjectRoot = ".", [string]$UtilsRel = "utils")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
$PY = "python"
$script = Join-Path $ROOT "scripts\diagnostics\analyze_utils.py"
Write-Host ">>> ProjectRoot = $ROOT"
& $PY $script --root $ROOT --utils $UtilsRel
