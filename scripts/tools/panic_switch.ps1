Param(
    [string]$EnvPath
)
$ErrorActionPreference = 'Stop'

# resolve repo root (two levels up from /scripts/tools)
$repoRoot = (Get-Item (Join-Path $PSScriptRoot "..\..")).FullName

# find .env
if ($EnvPath) {
    $envFile = (Resolve-Path $EnvPath).Path
} else {
    $envFile = Join-Path $repoRoot ".env"
}

if (-not (Test-Path $envFile)) { throw ".env not found: $envFile" }

# backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $repoRoot (".env.bak_" + $timestamp)
Copy-Item $envFile $backup -Force

# read
$raw = Get-Content -LiteralPath $envFile -Raw -ErrorAction Stop

function Set-KeyValue([string]$text, [string]$key, [string]$value) {
    $pattern = "^[ \t]*$([Regex]::Escape($key))[ \t]*=.*?$"
    if ($text -imatch $pattern) {
        return [Regex]::Replace($text, $pattern, "$key=$value", 'Multiline, IgnoreCase')
    } else {
        return ($text.TrimEnd() + "`r`n$key=$value`r`n")
    }
}

# force safe mode
$raw = Set-KeyValue $raw 'TRADE_ENABLED' '0'
$raw = Set-KeyValue $raw 'PAPER_TRADING' '1'

Set-Content -LiteralPath $envFile -Value $raw -Encoding utf8

Write-Host "PANIC ON: TRADE_ENABLED=0 (paper mode enforced)" -ForegroundColor Yellow
Write-Host "Backup: $backup"
