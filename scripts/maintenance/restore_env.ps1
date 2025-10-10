param([string]$ProjectRoot = ".")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host ">>> ProjectRoot = $ROOT"

$envPath = Join-Path $ROOT ".env"
$example = Join-Path $ROOT ".env.example"

if (Test-Path $envPath) {
    Write-Host "[OK] .env already exists: $envPath"
    exit 0
}

if (Test-Path $example) {
    Copy-Item -LiteralPath $example -Destination $envPath -Force
    Write-Host "[RESTORE] Copied .env.example -> .env"
} else {
    # Fallback: create a minimal safe .env
    $content = @"
# Auto-generated minimal .env (safe defaults)
PAPER_TRADING=1
TRADE_ENABLED=0
TESTNET=0
SYMBOL=BTCUSDT
STRATEGY=ema_rsi_atr
TIMEFRAME=1m
LOG_LEVEL=INFO
BINANCE_API_KEY=
BINANCE_API_SECRET=
"@
    Set-Content -LiteralPath $envPath -Value $content -Encoding UTF8
    Write-Host "[CREATE] Wrote minimal .env with safe defaults."
}

Write-Host "[DONE] .env ready at: $envPath"
