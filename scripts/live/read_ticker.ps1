# scripts/live/read_ticker.ps1
param(
  [string]$Symbol = $env:SYMBOL
)

$ErrorActionPreference = 'Stop'

if (-not $Symbol) { $Symbol = "BTCUSDT" }

$useTestnet = ($env:BINANCE_TESTNET -as [string])
if ($useTestnet) { $useTestnet = $useTestnet.ToLower() }
$base = "https://api.binance.com"
if ($useTestnet -in @("1","true","yes","y")) { $base = "https://testnet.binance.vision" }

$uri = "$base/api/v3/ticker/bookTicker?symbol=$Symbol"
Write-Host "GET $uri"
try {
  $r = Invoke-RestMethod -Uri $uri -Method GET -TimeoutSec 10
  $out = [PSCustomObject]@{
    ok = $true
    testnet = ($base -like "*testnet*")
    symbol = $Symbol
    bidPrice = $r.bidPrice
    askPrice = $r.askPrice
  }
  $out | ConvertTo-Json -Depth 5
  exit 0
} catch {
  $out = [PSCustomObject]@{
    ok = $false
    error = $_.Exception.Message
    symbol = $Symbol
    url = $uri
  }
  $out | ConvertTo-Json -Depth 5
  exit 1
}
