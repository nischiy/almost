param(
  [string]$ProjectRoot = ".",
  [string]$Python = "python",   # or "py -3"
  [switch]$WhatIf
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
$script = Join-Path $PSScriptRoot "remove_bridge.py"

Write-Host ">>> ProjectRoot = $ROOT"
Write-Host ">>> WhatIf: $($WhatIf.IsPresent)"

$argWhatIf = @()
if ($WhatIf) { $argWhatIf = @("--whatif") }

& $Python $script "--root" $ROOT @argWhatIf
if ($LASTEXITCODE -ne 0) { throw "Refactor failed with exit code $LASTEXITCODE" }
