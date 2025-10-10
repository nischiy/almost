param([string]$ProjectRoot = ".")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host ">>> ProjectRoot = $ProjectRoot"

$candDirs = @("core\logic","core\strategies","strategies","app\logic","app\strategies")
foreach ($d in $candDirs) {
    $full = Join-Path $ProjectRoot $d
    if (Test-Path $full) {
        Write-Host "`n[$d]"
        Get-ChildItem -LiteralPath $full -Recurse -File -Filter *.py -ErrorAction SilentlyContinue `
            | Where-Object { $_.FullName -notmatch '\\__pycache__\\' } `
            | ForEach-Object { Write-Host (" - " + $_.FullName) }
    }
}
$coreStrategy = Join-Path $ProjectRoot "core\strategy.py"
if (Test-Path $coreStrategy) {
    Write-Host "`n[core] explicit file:"
    Write-Host (" - " + (Resolve-Path -LiteralPath $coreStrategy).Path)
}
Write-Host "`nTip: Use cleanup_strategies.ps1 -Keep <file.py> to keep exactly one file in core\logic."
