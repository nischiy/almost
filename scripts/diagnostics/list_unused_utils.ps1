param(
    [string]$ProjectRoot = ".",
    [string]$UtilsRel = "utils"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
$UTILS = Join-Path $ROOT $UtilsRel
if (!(Test-Path $UTILS)) { throw "Utils folder not found: $UTILS" }

Write-Host ">>> ProjectRoot = $ROOT"
Write-Host ">>> UtilsDir    = $UTILS"

# Collect utils modules
$utilsMods = Get-ChildItem -Path $UTILS -Filter "*.py" -File | ForEach-Object { $_.BaseName }

# Search python files for imports referencing 'utils.<name>'
$allPy = Get-ChildItem -Path $ROOT -Filter "*.py" -File -Recurse | Where-Object { $_.FullName -notmatch "\\.venv\\|\\tests\\\\" }
$usage = @{}
foreach ($m in $utilsMods) { $usage[$m] = 0 }

foreach ($f in $allPy) {
    $text = Get-Content -LiteralPath $f.FullName -Raw
    foreach ($m in $utilsMods) {
        if ($text -match "(?m)(^|\s)from\s+utils\s+import\s+$m\b|(?m)\butils\.$m\b") {
            $usage[$m]++
        }
    }
}

$unused = @()
foreach ($k in $usage.Keys) {
    if ($usage[$k] -eq 0) { $unused += $k }
}

if ($unused.Count -eq 0) {
    Write-Host "[OK] All utils modules are referenced somewhere."
} else {
    Write-Warning "Unused utils modules (no imports found):"
    $unused | Sort-Object | ForEach-Object { Write-Host (" - " + $_ + ".py") }
}
