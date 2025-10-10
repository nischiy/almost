# scripts/check_all.ps1
[CmdletBinding()]
param(
    [switch]$WithSafety
)

$ErrorActionPreference = "Stop"

Write-Host ">>> 1) Preflight"
.\scripts\preflight.ps1

Write-Host "`n>>> 2) Core+Contract tests"
pytest -q -vv

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($WithSafety) {
    Write-Host "`n>>> 3) Optional safety tests"
    $env:RUN_SAFETY_TESTS = "1"
    pytest -q -vv tests_opt
    $code = $LASTEXITCODE
    Remove-Item Env:RUN_SAFETY_TESTS -ErrorAction Ignore
    if ($code -ne 0) { exit $code }
}

Write-Host "`nAll checks passed."
