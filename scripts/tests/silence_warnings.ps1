param([string]$ProjectRoot = ".")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host ">>> ProjectRoot = $ProjectRoot"

function Patch-FileText {
    param([string]$Path, [scriptblock]$Transform)
    if (!(Test-Path $Path)) { return $false }
    $text = Get-Content -LiteralPath $Path -Raw
    $new  = & $Transform $text
    if ($new -ne $text) {
        $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
        $bak = "$Path.bak.$stamp"
        Copy-Item -LiteralPath $Path -Destination $bak -Force
        Set-Content -LiteralPath $Path -Value $new -Encoding UTF8
        Write-Host "[PATCH] $Path  (backup: $bak)"
        return $true
    }
    return $false
}

# 1) tests\conftest.py -> datetime.utcnow -> datetime.now(datetime.UTC); freq="T" -> "min"
$conftest = Join-Path $ProjectRoot "tests\conftest.py"
[void](Patch-FileText -Path $conftest -Transform {
    param($t)
    $t = $t -replace 'datetime\.utcnow\(\)', 'datetime.now(datetime.UTC)'
    $t = $t -replace 'freq="T"', 'freq="min"'
    return $t
})

# 2) tests\test_risk_gate.py -> freq="T" -> "min"
$riskgate = Join-Path $ProjectRoot "tests\test_risk_gate.py"
[void](Patch-FileText -Path $riskgate -Transform {
    param($t)
    $t = $t -replace 'freq="T"', 'freq="min"'
    return $t
})

Write-Host "[DONE] Warnings silenced where applicable."
