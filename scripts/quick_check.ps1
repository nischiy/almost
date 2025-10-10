
param(
  [string]$Symbol = "BTCUSDT",
  [string]$Interval = "1h",
  [int]$Limit = 1000
)

$ErrorActionPreference = "Stop"

# Ensure tmp exists
$root = (Get-Location).Path
$tmp = Join-Path $root "tmp"
if (-not (Test-Path $tmp)) { New-Item -ItemType Directory -Path $tmp | Out-Null }

# Set env for child
$env:SYMBOL = $Symbol
$env:INTERVAL = $Interval
$env:LIMIT = "$Limit"

# Force UTF-8 to avoid encoding glitches
$env:PYTHONIOENCODING = "utf-8"

# Run
$py = Join-Path $root "tmp\quick_bt.py"
if (-not (Test-Path $py)) {
  Write-Error "quick_bt.py not found at $py"
}

python $py
