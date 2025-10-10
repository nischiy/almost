param(
    [string]$ProjectRoot = ".",
    [string]$UtilsRel = "utils"  # allow "app\utils" if needed
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
$UTILS = Join-Path $ROOT $UtilsRel
if (!(Test-Path $UTILS)) { throw "Utils folder not found: $UTILS" }

Write-Host ">>> ProjectRoot = $ROOT"
Write-Host ">>> UtilsDir    = $UTILS"

# Ensure targets
$docs = Join-Path $ROOT "docs\readmes"
$scripts = Join-Path $ROOT "scripts"
$release = Join-Path $scripts "release"
foreach ($d in @($docs,$scripts,$release)) { if (!(Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null } }

# Move non-.py from utils
$notesMoved = 0
$scriptsMoved = 0

Get-ChildItem -Path $UTILS -File | ForEach-Object {
    $ext = $_.Extension.ToLowerInvariant()
    $name = $_.Name
    $src = $_.FullName

    if ($ext -eq ".py") { return }
    elseif ($ext -eq ".ps1") {
        $dst = Join-Path $release $name
        Move-Item -LiteralPath $src -Destination $dst -Force
        Write-Host "[MOVE] SCRIPT: $src -> $dst"
        $scriptsMoved++
    }
    elseif ($ext -eq ".md" -or $name -match "NOTE|PATCH|README") {
        $dst = Join-Path $docs $name
        Move-Item -LiteralPath $src -Destination $dst -Force
        Write-Host "[MOVE] NOTE : $src -> $dst"
        $notesMoved++
    }
    else {
        Write-Warning "Unknown non-PY file in utils: $name (left in place)"
    }
}

Write-Host ("[DONE] Moved notes: {0} | scripts: {1}" -f $notesMoved, $scriptsMoved)
