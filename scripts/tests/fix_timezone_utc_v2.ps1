param([string]$ProjectRoot = ".")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host ">>> ProjectRoot = $ROOT"

function Save-Backup([string]$Path, [string]$Content) {
    $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $bak = "$Path.bak.$stamp"
    Set-Content -LiteralPath $bak -Value $Content -Encoding UTF8
    Write-Host "[BACKUP] $bak"
}

$conf = Join-Path $ROOT "tests\conftest.py"
if (!(Test-Path $conf)) { throw "File not found: $conf" }

$text = Get-Content -LiteralPath $conf -Raw
$orig = $text

# Ensure import line exists somewhere near the top.
if ($text -notmatch "(?m)^\s*from\s+datetime\s+import\s+timezone\b") {
    # Insert after any shebang/encoding or initial imports; else at top.
    $lines = $text -split "`r?`n"
    $insertIdx = 0
    for ($i=0; $i -lt [Math]::Min($lines.Length, 20); $i++) {
        if ($lines[$i] -match "^\s*(import|from)\s+") { $insertIdx = $i + 1 }
        elseif ($lines[$i] -match "^\s*$") { $insertIdx = $i + 1 }
        else { break }
    }
    $lines = @($lines[0..($insertIdx-1)]) + @("from datetime import timezone") + @($lines[$insertIdx..($lines.Length-1)])
    $text = ($lines -join "`r`n")
}

# Replace datetime.UTC -> timezone.utc everywhere
$text = $text -replace "\bdatetime\.UTC\b", "timezone.utc"

if ($text -ne $orig) {
    Save-Backup -Path $conf -Content $orig
    Set-Content -LiteralPath $conf -Value $text -Encoding UTF8
    Write-Host "[PATCH] $conf"
} else {
    Write-Host "[OK] No changes required."
}

Write-Host "[DONE] Timezone hotfix v2 applied."
