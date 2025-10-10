param(
    [string]$Symbol = $env:SYMBOL,
    [int]$IntervalSec = 3
)
$ErrorActionPreference = "Stop"
if (-not $Symbol) { $Symbol = "BTCUSDT" }

function Get-JsonFromOutput {
    param([string[]]$Lines)
    # Find first line that looks like JSON and convert
    foreach ($line in $Lines) {
        $trim = $line.Trim()
        if ($trim.StartsWith("{") -or $trim.StartsWith("[")) {
            try { return $trim | ConvertFrom-Json } catch {}
        }
    }
    return $null
}

Write-Host "=== TradeWatch ===" -ForegroundColor Cyan
Write-Host "Symbol: $Symbol  | interval: ${IntervalSec}s" -ForegroundColor DarkCyan
Write-Host "Press Q to quit..."

while ($true) {
    # Quit on key 'Q'
    if ([console]::KeyAvailable) {
        $k = [console]::ReadKey($true)
        if ($k.Key -eq 'Q') { break }
    }

    # 1) Ticker
    $tickerOut = & "$PSScriptRoot\..\live\read_ticker.ps1" -Symbol $Symbol 2>$null
    $ticker = Get-JsonFromOutput -Lines $tickerOut

    # 2) Account (unsigned fields ok; script itself does signed call if keys available)
    $acctOut = & "$PSScriptRoot\..\live\check_account.ps1" 2>$null
    $acct = Get-JsonFromOutput -Lines $acctOut

    # 3) Last smoke backtest
    $smokeFile = Join-Path (Resolve-Path "$PSScriptRoot\..\..").Path "logs\smoke\last.json"
    $smoke = $null
    if (Test-Path $smokeFile) {
        try { $smoke = Get-Content $smokeFile -Raw | ConvertFrom-Json } catch {}
    }

    Clear-Host
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "=== TradeWatch @ $now ===" -ForegroundColor Cyan
    if ($ticker -and $ticker.ok) {
        $bid = [decimal]$ticker.bidPrice
        $ask = [decimal]$ticker.askPrice
        $mid = [decimal]0
        if ($ask -ne 0) { $mid = ($bid + $ask) / 2 }
        $spr = if ($mid -ne 0) { [math]::Round((($ask - $bid)/$mid)*10000, 2) } else { 0 }
        "{0,-10} bid {1,12} | ask {2,12} | spread {3,6} bps" -f $ticker.symbol, $bid, $ask, $spr
    } else {
        Write-Host "Ticker: N/A" -ForegroundColor Yellow
    }

    $tradeEnabled = ($env:TRADE_ENABLED | ForEach-Object { $_.ToString().ToLower() }) -eq "1"
    $testnet = ($env:BINANCE_TESTNET | ForEach-Object { $_.ToString().ToLower() }) -eq "true"
    Write-Host ("Mode: {0} | TradeEnabled: {1}" -f ($(if($testnet){"TESTNET"}else{"MAINNET"}), $tradeEnabled)) `
        -ForegroundColor ($(if($testnet){"Yellow"}else{"Green"}))

    if ($acct -and $acct.ok) {
        $bal = $acct.balances | Select-Object -First 5
        Write-Host "Balances (top):"
        foreach ($b in $bal) {
            "{0,-6} free={1,-14} locked={2}" -f $b.asset, $b.free, $b.locked
        }
    } else {
        Write-Host "Account: N/A" -ForegroundColor Yellow
    }

    if ($smoke -and $smoke.ok) {
        $bt = $smoke.backtest
        if ($bt) {
            Write-Host ("Backtest: {0} | trades={1} | pnl={2:N4} | maxDD={3:N4}" -f $bt.name, $bt.trades, $bt.gross_pnl, $bt.max_dd)
        }
    }
    Start-Sleep -Seconds $IntervalSec
}
