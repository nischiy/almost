param(
  [string]$ProjectRoot = "."
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$envPath = Join-Path -Path $root -ChildPath ".env"
if (-not (Test-Path -LiteralPath $envPath)) {
  throw ".env not found at $envPath"
}

# Load current lines preserving comments
$lines = Get-Content -LiteralPath $envPath -ErrorAction Stop

function Set-Or-Append([string]$key, [string]$value) {
  $pattern = "^\s*{0}\s*=" -f [regex]::Escape($key)
  $idx = ($lines | Select-String -Pattern $pattern -SimpleMatch).LineNumber
  if ($idx) {
    $i = [int]$idx - 1
    $lines[$i] = "{0}={1}" -f $key, $value
  } else {
    $lines += "{0}={1}" -f $key, $value
  }
}

# Ensure risk keys have numeric values
Set-Or-Append -key "RISK_MAX_DD_PCT_DAY" -value "3.0"
Set-Or-Append -key "RISK_MAX_TRADES_PER_DAY" -value "20"
Set-Or-Append -key "RISK_MAX_CONSEC_LOSSES" -value "3"
Set-Or-Append -key "RISK_MIN_EQUITY_USD" -value "50"

# Save back
Set-Content -LiteralPath $envPath -Value $lines -Encoding UTF8 -NoNewline:$false
Write-Host "Updated .env risk keys."
