
param(
  [string[]]$Keys = @(
    "RISK_MAX_DD_PCT_DAY",
    "RISK_MAX_TRADES_PER_DAY",
    "RISK_MAX_CONSEC_LOSSES",
    "RISK_MIN_EQUITY_USD"
  )
)
$ErrorActionPreference = "Stop"
foreach ($k in $Keys) {
  if (Test-Path Env:$k) {
    Remove-Item Env:$k -ErrorAction SilentlyContinue
  }
}
Write-Host "Cleared conflicting in-process ENV vars for risk keys."
