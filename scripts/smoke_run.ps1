Param(
    [string]$ProjectRoot = ".",
    [string]$Symbol = "BTCUSDT",
    [string]$Interval = "1m"
)
Set-Location $ProjectRoot
$env:PAPER_TRADING="true"
$env:TRADE_ENABLED="false"
$env:SYMBOL=$Symbol
$env:INTERVAL=$Interval
Write-Host ">>> Smoke run (paper=false) with $Symbol@$Interval"
python .\main.py
