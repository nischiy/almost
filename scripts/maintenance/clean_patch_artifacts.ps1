param(
    [string]$ProjectRoot = ".",
    [switch]$WhatIf
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host ">>> ProjectRoot = $ProjectRoot"
Write-Host ">>> WhatIf: $($WhatIf.IsPresent)"

# Patterns to remove: temporary patch/fix scripts and backups
$scriptDirs = @("scripts")
$patterns = @(
    "scripts\patch_*.ps1",
    "scripts\fix_*.ps1",
    "scripts\tests\organize_tests.ps1",
    "_backup_*.zip",
    "*.bak.*"
)

$removed = 0
foreach ($pat in $patterns) {
    $glob = Join-Path $ProjectRoot $pat
    Get-ChildItem -Path $glob -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        if ($WhatIf) {
            Write-Host "[WhatIf] Would remove: $($_.FullName)"
        } else {
            Remove-Item -LiteralPath $_.FullName -Force
            Write-Host "[DEL] $($_.FullName)"
        }
        $removed++
    }
}

Write-Host "[DONE] Items processed: $removed"
if ($WhatIf) { Write-Host "Run again without -WhatIf to actually delete." }
