param(
    [switch]$Strict
)
$ErrorActionPreference = "Stop"
$repo = Resolve-Path "$PSScriptRoot\..\.."
Push-Location $repo
try {
    Write-Host ">> Preflight" -ForegroundColor Cyan
    if ($Strict) {
        & "$repo\scripts\preflight.ps1" -Strict
    } else {
        & "$repo\scripts\preflight.ps1"
    }

    Write-Host ">> Smoke pipeline" -ForegroundColor Cyan
    & "$repo\scripts\smoke\run_smoke_pipeline.ps1"

    Write-Host ">> Paper summary" -ForegroundColor Cyan
    & "$repo\scripts\paper\report.ps1"

    Write-Host "Health OK." -ForegroundColor Green
} finally {
    Pop-Location
}
