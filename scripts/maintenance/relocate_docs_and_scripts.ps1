param(
    [string]$ProjectRoot = ".",
    [switch]$WhatIf
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-ProjectPath([string]$root) { (Resolve-Path -LiteralPath $root).Path }
function Ensure-Dir([string]$path) { if (!(Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null } }

$ROOT = Resolve-ProjectPath $ProjectRoot
Write-Host ">>> ProjectRoot = $ROOT"
Write-Host ">>> WhatIf: $($WhatIf.IsPresent)"

$docsDir = Join-Path $ROOT "docs\readmes"
$scriptsRoot = Join-Path $ROOT "scripts"
$testsDir = Join-Path $scriptsRoot "tests"
$maintDir = Join-Path $scriptsRoot "maintenance"
$releaseDir = Join-Path $scriptsRoot "release"
$diagDir = Join-Path $scriptsRoot "diagnostics"
$migratedRoot = Join-Path $scriptsRoot "migrated_root"

# Ensure structure
$dirs = @($docsDir,$scriptsRoot,$testsDir,$maintDir,$releaseDir,$diagDir,$migratedRoot)
foreach ($d in $dirs) { Ensure-Dir $d }

# Counters
[int]$movedReadmes = 0
[int]$movedScripts = 0

# 1) Move README*/PATCH* notes from root to docs\readmes
$readmePatterns = @(
    "README*.md","README*.txt",
    "PATCH*.md","PATCH*.txt"
)
foreach ($pat in $readmePatterns) {
    Get-ChildItem -Path (Join-Path $ROOT $pat) -File -ErrorAction SilentlyContinue | ForEach-Object {
        $src = $_.FullName
        $dst = Join-Path $docsDir $_.Name
        if ($WhatIf) {
            Write-Host "[WhatIf] Move README: $src -> $dst"
        } else {
            Move-Item -LiteralPath $src -Destination $dst -Force
            Write-Host "[MOVE] README: $src -> $dst"
        }
        $movedReadmes++
    }
}

# 2) Move any *.ps1 scripts from ROOT into scripts/<bucket>
Get-ChildItem -Path (Join-Path $ROOT "*.ps1") -File -ErrorAction SilentlyContinue | ForEach-Object {
    $src = $_.FullName
    $name = $_.Name.ToLowerInvariant()
    $dstDir = $migratedRoot
    if ($name -match "test|pytest") { $dstDir = $testsDir }
    elseif ($name -match "maint|clean|cleanup|organize|relocat") { $dstDir = $maintDir }
    elseif ($name -match "make|release|archive|pack") { $dstDir = $releaseDir }
    elseif ($name -match "diag|verify|list|find") { $dstDir = $diagDir }
    $dst = Join-Path $dstDir $_.Name
    if ($WhatIf) {
        Write-Host "[WhatIf] Move SCRIPT: $src -> $dst"
    } else {
        Move-Item -LiteralPath $src -Destination $dst -Force
        Write-Host "[MOVE] SCRIPT: $src -> $dst"
    }
    $movedScripts++
}

# 3) Report leftovers
$leftover = @()
$leftover += Get-ChildItem -Path (Join-Path $ROOT "README*") -File -ErrorAction SilentlyContinue
$leftover += Get-ChildItem -Path (Join-Path $ROOT "PATCH*") -File -ErrorAction SilentlyContinue
$leftover += Get-ChildItem -Path (Join-Path $ROOT "*.ps1") -File -ErrorAction SilentlyContinue

if ($leftover.Count -gt 0) {
    Write-Warning ("Left in root (should be empty for README/ps1): " + ($leftover | ForEach-Object { $_.Name } | Sort-Object | ForEach-Object { "`n - $_" }))
} else {
    Write-Host "[OK] Root is clean of README and *.ps1"
}

Write-Host ("[SUMMARY] Readmes moved: {0} | Scripts moved: {1}" -f $movedReadmes, $movedScripts)
Write-Host "[DONE] Relocation complete."
