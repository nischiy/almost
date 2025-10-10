
param([string]$ProjectRoot = ".")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$pf = Join-Path $root "tools\preflight\preflight_all.py"
$bak = $pf + ".bak"
if (-not (Test-Path -LiteralPath $bak)) { throw "Backup not found: $bak" }
Copy-Item -LiteralPath $bak -Destination $pf -Force
Write-Host "Reverted preflight_all.py from backup."
