# scripts/tools/trade.ps1  (convenience runner)
param(
  [Parameter(Position=0)][string]$Side = "BUY",
  [Parameter(Position=1)][string]$Type = "MARKET",
  [Parameter(Position=2)][string]$Price = ""
)
$ErrorActionPreference = "Stop"
$env:SIDE = $Side
$env:TYPE = $Type
if ($Type.ToUpper() -eq "LIMIT" -and $Price -ne "") { $env:PRICE = $Price }

$py = "$PWD\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

& $py "scripts/diagnostics/trade_once.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
