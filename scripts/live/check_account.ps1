[CmdletBinding()]
param(
    [switch]$Testnet
)
$ErrorActionPreference = 'Stop'
# Force TLS 1.2 for older PS
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Repo root (this script is in scripts\live)
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# Auto-load .env if present
$dotenv = Join-Path $repo 'tools\ps\LoadDotEnv.ps1'
$envPath = Join-Path $repo '.env'
if (Test-Path -LiteralPath $dotenv) {
    . $dotenv
    try { Load-DotEnv -FilePath $envPath | Out-Null } catch {}
}

# Safe-read BINANCE_TESTNET (treat $null as empty string)
$envVal = "" + $env:BINANCE_TESTNET
$fromEnv = $false
if ($envVal) {
    $lower = $envVal.ToLower()
    if ($lower -in @('1','true','yes','y')) { $fromEnv = $true }
}
$useTestnet = $Testnet.IsPresent -or $fromEnv

$base = if ($useTestnet) { 'https://testnet.binance.vision' } else { 'https://api.binance.com' }
$apiKey    = $env:BINANCE_API_KEY
$apiSecret = $env:BINANCE_API_SECRET
$hasKey    = -not [string]::IsNullOrWhiteSpace($apiKey)
$hasSecret = -not [string]::IsNullOrWhiteSpace($apiSecret)
$nowUtc    = (Get-Date).ToUniversalTime().ToString('o')

if (-not ($hasKey -and $hasSecret)) {
    [ordered]@{
        ok          = $false
        testnet     = $useTestnet
        base        = $base
        now_utc     = $nowUtc
        has_key     = $hasKey
        has_secret  = $hasSecret
        balances    = @()
        error       = 'Missing BINANCE_API_KEY / BINANCE_API_SECRET (set in .env)'
        status_code = $null
    } | ConvertTo-Json -Depth 6
    exit 2
}

$timestamp = [int64]([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())
$recv = 5000
$query = "timestamp=$timestamp&recvWindow=$recv"

# HMAC-SHA256 signature
$hmac = New-Object System.Security.Cryptography.HMACSHA256
$hmac.Key = [Text.Encoding]::UTF8.GetBytes($apiSecret)
$signature = ($hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($query)) | ForEach-Object { $_.ToString("x2") }) -join ""

$url = "$base/api/v3/account?$query&signature=$signature"

try {
    $resp = Invoke-RestMethod -Uri $url -Headers @{ 'X-MBX-APIKEY' = $apiKey } -Method Get -TimeoutSec 15
    $balances = @()
    foreach ($b in $resp.balances) {
        # show only non-zero balances
        if ([decimal]$b.free -gt 0 -or [decimal]$b.locked -gt 0) {
            $balances += [ordered]@{ asset = $b.asset; free = $b.free; locked = $b.locked }
        }
    }
    [ordered]@{
        ok          = $true
        testnet     = $useTestnet
        base        = $base
        now_utc     = $nowUtc
        has_key     = $true
        has_secret  = $true
        balances    = $balances
        status_code = 200
    } | ConvertTo-Json -Depth 6
    exit 0
}
catch {
    $status = $null
    $body = $null
    if ($_.Exception.Response) {
        try { $status = [int]$_.Exception.Response.StatusCode } catch {}
        try {
            $reader = New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())
            $body = $reader.ReadToEnd()
        } catch {}
    }
    [ordered]@{
        ok          = $false
        testnet     = $useTestnet
        base        = $base
        now_utc     = $nowUtc
        has_key     = $hasKey
        has_secret  = $hasSecret
        balances    = @()
        error       = $_.Exception.Message
        status_code = $status
        body        = $body
    } | ConvertTo-Json -Depth 6
    exit 1
}
