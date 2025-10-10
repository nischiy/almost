param(
  [string]$Intervals = "15m,1h,4h",
  [int]$Limit = 1000
)

$repo = (Split-Path -Parent $PSScriptRoot)  # -> ...\scripts
$quickCheck = Join-Path $repo "quick_check.ps1"
$quickSweep = Join-Path $repo "quick_sweep.ps1"

if (-not (Test-Path $quickCheck)) { throw "Missing scripts\quick_check.ps1" }
if (-not (Test-Path $quickSweep)) { throw "Missing scripts\quick_sweep.ps1" }

Write-Host "=== BTC-only quick check (BTCUSDT / 1h / 1000) ==="
& $quickCheck | Out-Host

Write-Host ""
Write-Host "=== BTC-only sweep ==="
& $quickSweep -Symbols "BTCUSDT" -Intervals $Intervals -Limit $Limit
