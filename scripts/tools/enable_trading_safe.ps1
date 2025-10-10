Param(
    [switch]$TestnetOnly,
    [switch]$ForceMainnet,
    [string]$EnvPath
)
$ErrorActionPreference = 'Stop'

$repoRoot = (Get-Item (Join-Path $PSScriptRoot "..\..")).FullName
if ($EnvPath) {
    $envFile = (Resolve-Path $EnvPath).Path
} else {
    $envFile = Join-Path $repoRoot ".env"
}
if (-not (Test-Path $envFile)) { throw ".env not found: $envFile" }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $repoRoot (".env.bak_" + $timestamp)
Copy-Item $envFile $backup -Force

$raw = Get-Content -LiteralPath $envFile -Raw -ErrorAction Stop

function Set-KeyValue([string]$text, [string]$key, [string]$value) {
    $pattern = "^[ \t]*$([Regex]::Escape($key))[ \t]*=.*?$"
    if ($text -imatch $pattern) {
        return [Regex]::Replace($text, $pattern, "$key=$value", 'Multiline, IgnoreCase')
    } else {
        return ($text.TrimEnd() + "`r`n$key=$value`r`n")
    }
}

if ($TestnetOnly) {
    $raw = Set-KeyValue $raw 'BINANCE_TESTNET' 'true'
    $raw = Set-KeyValue $raw 'TRADE_ENABLED' '1'
    Write-Host "Trading ENABLED on TESTNET." -ForegroundColor Green
} elseif ($ForceMainnet) {
    $raw = Set-KeyValue $raw 'BINANCE_TESTNET' 'false'
    $raw = Set-KeyValue $raw 'TRADE_ENABLED' '1'
    Write-Warning "Trading ENABLED on MAINNET (ForceMainnet used)."
} else {
    throw "Refusing to enable trading on MAINNET without -ForceMainnet or on TESTNET without -TestnetOnly."
}

Set-Content -LiteralPath $envFile -Value $raw -Encoding utf8

Write-Host "Backup: $backup"
