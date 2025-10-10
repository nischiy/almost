param(
    [string]$ProjectRoot = ".",
    [switch]$WhatIf,
    [switch]$ApplyRiskGuardMove  # if set: replace imports utils.risk_guard -> core.risk_guard and delete utils\risk_guard.py
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-ProjectPath([string]$root) { (Resolve-Path -LiteralPath $root).Path }
function Read-Json([string]$path) { Get-Content -LiteralPath $path -Raw | ConvertFrom-Json }

$ROOT = Resolve-ProjectPath $ProjectRoot
Write-Host ">>> ProjectRoot = $ROOT"
Write-Host ">>> WhatIf: $($WhatIf.IsPresent)"
Write-Host ">>> ApplyRiskGuardMove: $($ApplyRiskGuardMove.IsPresent)"

$report = Join-Path $ROOT "docs\readmes\UTILS_AUDIT.json"
if (!(Test-Path $report)) { throw "Audit file not found: $report. Run the utils audit first." }
$data = Read-Json $report

# 1) Remove unused (usage==0 AND recommendation starts with 'REVIEW')
$toDelete = @()
foreach ($r in $data) {
    if (($r.usage -eq 0) -and ($r.recommendation -like "REVIEW*")) {
        $toDelete += $r.path
    }
}
if ($toDelete.Count -gt 0) {
    Write-Host "=== Unused modules to delete ==="
    $toDelete | ForEach-Object { Write-Host " - $_" }
    foreach ($rel in $toDelete) {
        $abs = Join-Path $ROOT $rel
        if (Test-Path $abs) {
            if ($WhatIf) {
                Write-Host "[WhatIf] DEL $abs"
            } else {
                Remove-Item -LiteralPath $abs -Force
                Write-Host "[DEL] $abs"
            }
        }
    }
} else {
    Write-Host "[OK] No unused utils modules to delete."
}

# 2) Optional: migrate utils.risk_guard -> core.risk_guard
if ($ApplyRiskGuardMove) {
    $ug = Join-Path $ROOT "utils\risk_guard.py"
    # Patch imports across repo
    $pyFiles = Get-ChildItem -Path $ROOT -Recurse -Filter "*.py" | Where-Object { $_.FullName -notmatch "\\.venv\\|\\tests\\\\" }
    foreach ($f in $pyFiles) {
        $t = Get-Content -LiteralPath $f.FullName -Raw
        $new = $t
        $new = $new -replace "(?m)^\s*from\s+utils\.risk_guard\s+import\s+", "from core.risk_guard import "
        $new = $new -replace "(?m)\butils\.risk_guard\b", "core.risk_guard"
        if ($new -ne $t) {
            if ($WhatIf) {
                Write-Host "[WhatIf] PATCH " $f.FullName
            } else {
                Set-Content -LiteralPath $f.FullName -Value $new -Encoding UTF8
                Write-Host "[PATCH] " $f.FullName
            }
        }
    }
    # Delete the utils\risk_guard.py if exists
    if (Test-Path $ug) {
        if ($WhatIf) {
            Write-Host "[WhatIf] DEL $ug"
        } else {
            Remove-Item -LiteralPath $ug -Force
            Write-Host "[DEL] $ug"
        }
    }
}

Write-Host "[DONE] Cleanup completed."
