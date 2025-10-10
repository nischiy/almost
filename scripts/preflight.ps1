# scripts/preflight.ps1
[CmdletBinding()]
param(
    [switch]$Strict  # If set, empty values are treated as missing (unless skip flags)
)

$ErrorActionPreference = "Stop"

function Ensure-Dir {
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
        Write-Host "Created $Path"
    } else {
        Write-Host "OK $Path"
    }
}

function Load-DotEnv {
    param([string]$Path = ".env")
    if (-not (Test-Path -LiteralPath $Path)) {
        return 0
    }
    $count = 0
    $lines = Get-Content -LiteralPath $Path -ErrorAction Stop
    foreach ($line in $lines) {
        if ($null -eq $line) { continue }
        $trim = $line.Trim()
        if ($trim -eq "" -or $trim.StartsWith("#") -or $trim.StartsWith(";")) { continue }
        # KEY=VALUE (keep VALUE as-is, strip surrounding quotes)
        if ($trim -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $key = $Matches[1]
            $val = $Matches[2].Trim()
            # strip surrounding quotes if present
            if (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
                $val = $val.Substring(1, $val.Length - 2)
            }
            # set for current process only (non-persistent)
            [System.Environment]::SetEnvironmentVariable($key, $val, "Process")
            $count += 1
        }
    }
    return $count
}

Write-Host "=== Preflight start ==="

# 0) Load .env into Process env (non-invasive)
$loaded = Load-DotEnv ".env"
if ($loaded -gt 0) {
    Write-Host "Loaded $loaded variables from .env"
} else {
    Write-Host ".env not found or empty (optional)"
}

# 1) Folders
Ensure-Dir "logs"
Ensure-Dir "models"

# Skip rules
$skipApi = $false
$pt = (Get-Item Env:PAPER_TRADING -ErrorAction Ignore)
if ($pt) { $skipApi = ($pt.Value -in @("1","true","True","on","ON","yes","YES")) }
$pfskip = (Get-Item Env:PRE_FLIGHT_SKIP_API -ErrorAction Ignore)
if ($pfskip) { $skipApi = $skipApi -or ($pfskip.Value -in @("1","true","True","on","ON","yes","YES")) }

# Helper: check one var
function Test-EnvVar {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [switch]$Optional
    )
    $item = Get-Item ("Env:" + $Name) -ErrorAction Ignore
    if (-not $item) {
        if ($Optional) { Write-Host "ENV $Name = (missing) [optional]" -ForegroundColor Yellow }
        else { Write-Warning "ENV missing: $Name"; return $false }
        return $true
    }
    $val = $item.Value
    if ($Strict -and (-not $val)) {
        if ($Optional) { Write-Host "ENV $Name = (empty) [optional]" -ForegroundColor Yellow }
        else { Write-Warning "ENV empty: $Name"; return $false }
    } else {
        Write-Host "ENV $Name = OK"
    }
    return $true
}

# 2) Checks
$allOk = $true

# BINANCE_API_*: optional when skipApi is true
if ($skipApi) {
    Test-EnvVar "BINANCE_API_KEY" -Optional | Out-Null
    Test-EnvVar "BINANCE_API_SECRET" -Optional | Out-Null
} else {
    if (-not (Test-EnvVar "BINANCE_API_KEY")) { $allOk = $false }
    if (-not (Test-EnvVar "BINANCE_API_SECRET")) { $allOk = $false }
}

# Testnet flag (should exist even in paper mode)
if (-not (Test-EnvVar "BINANCE_TESTNET")) { $allOk = $false }

# DB_URL is optional by default
Test-EnvVar "DB_URL" -Optional | Out-Null

Write-Host "=== Preflight done ==="
if (-not $allOk) { exit 2 }
