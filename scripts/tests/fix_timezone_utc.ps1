param([string]$ProjectRoot = ".")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host ">>> ProjectRoot = $ROOT"

function Patch-File {
    param([string]$Path, [scriptblock]$Transform)
    if (!(Test-Path $Path)) { return $false }
    $orig = Get-Content -LiteralPath $Path -Raw
    $new  = & $Transform $orig
    if ($new -ne $orig) {
        $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
        $bak = "$Path.bak.$stamp"
        Copy-Item -LiteralPath $Path -Destination $bak -Force
        Set-Content -LiteralPath $Path -Value $new -Encoding UTF8
        Write-Host "[PATCH] $Path (backup: $bak)"
        return $true
    } else {
        Write-Host "[OK] $Path already clean"
        return $false
    }
}

$conftest = Join-Path $ROOT "tests\conftest.py"
[void](Patch-File -Path $conftest -Transform {
    param($t)
    # Ensure import
    if ($t -notmatch "(?m)^\s*from\s+datetime\s+import\s+timezone\b") {
        # insert after first datetime import if present, else at top
        if ($t -match "(?m)^\s*from\s+datetime\s+import\s+[^\n]+") {
            $t = [regex]::Replace($t, "(?m)^\s*from\s+datetime\s+import\s+[^\n]+", "$0`nfrom datetime import timezone", 1)
        } else {
            $t = "from datetime import timezone`n" + $t
        }
    }
    # Replace datetime.UTC -> timezone.utc
    $t = $t -replace '\bdatetime\.UTC\b', 'timezone.utc'
    return $t
})

Write-Host "[DONE] Timezone hotfix applied."
