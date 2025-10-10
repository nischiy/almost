param(
    [int]$N = 20,
    [int]$IntervalSeconds = 1,
    [switch]$NoSleep
)
$ErrorActionPreference = "Stop"
Write-Host "=== Paper dry-run loop ==="
$repo = (Resolve-Path ".").Path

& "$PSScriptRoot\..\preflight.ps1" -Strict | Out-Host

$venvPy = Join-Path $repo ".venv\Scripts\python.exe"
if (Test-Path $venvPy) { $python = $venvPy } else { $python = "python" }

$opts = @("--n", $N, "--interval-seconds", $IntervalSeconds)
if ($NoSleep) { $opts += "--no-sleep" }

& $python (Join-Path $repo "tools\paper\dryrun_loop.py") @opts

$orders = Join-Path $repo "logs\paper\orders.csv"
if (Test-Path $orders) {
    Write-Host "OK. Orders appended: $orders"
    Get-Content $orders | Select-Object -Last 10
} else {
    Write-Warning "orders.csv not found."
}