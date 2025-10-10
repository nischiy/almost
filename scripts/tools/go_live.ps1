# scripts/tools/go_live.ps1 (auto-exits aware)
param(
  [Parameter(Mandatory=$true, Position=0)][ValidateSet("BUY","SELL")][string]$Side,
  [Parameter(Mandatory=$true, Position=1)][ValidateSet("MARKET","LIMIT")][string]$Type,
  [Parameter(Position=2)][string]$Price,
  [switch]$AutoExits,
  [Parameter()][double]$SL,
  [Parameter()][double]$TP
)
$ErrorActionPreference = "Stop"
if (-not $env:API_KEY -or -not $env:API_SECRET) { throw "Set API_KEY and API_SECRET" }
if ($env:DRY_RUN_ONLY -ne "0") { throw "Set DRY_RUN_ONLY=0 for live trading" }
if (-not $env:SYMBOL) { $env:SYMBOL = "BTCUSDT" }

$env:SIDE = $Side
$env:TYPE = $Type
if ($Type -eq "LIMIT" -and $Price) { $env:PRICE = $Price }

$py = "$PWD\.venv\Scripts\python.exe"; if (-not (Test-Path $py)) { $py = "python" }

# choose CLI: auto or manual exits
$useAuto = $AutoExits.IsPresent -or ($env:SEND_DEFAULT_EXITS -eq "1")
if ($useAuto) {
  $entry = & $py "scripts/diagnostics/order_send_live_auto_cli.py"
  Write-Host ($entry | Out-String)
} else {
  $entry = & $py "scripts/diagnostics/order_send_live_cli.py"
  Write-Host ($entry | Out-String)
  if ($SL -or $TP) {
    if ($Side -eq "BUY") { $env:SIDE = "BUY" } else { $env:SIDE = "SELL" }
    if ($SL) { $env:SL_PRICE = "$SL" }
    if ($TP) { $env:TP_PRICE = "$TP" }
    $env:SEND_EXITS = "1"
    $ex = & $py "scripts/diagnostics/set_tp_sl_cli.py"
    Write-Host ($ex | Out-String)
  }
}
