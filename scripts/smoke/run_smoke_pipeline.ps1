param(
    [switch]$SkipPreflight,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "=== Smoke pipeline ==="

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Resolve-Path (Join-Path $ScriptDir "..\..")
Write-Host "Repo: $RepoRoot"
Set-Location $RepoRoot

$SmokeDir = Join-Path $RepoRoot "logs\smoke"
if (-not (Test-Path $SmokeDir)) {
    New-Item -ItemType Directory -Path $SmokeDir | Out-Null
}

if (-not $SkipPreflight) {
    Write-Host ">> Preflight (Strict)"
    & .\scripts\preflight.ps1 -Strict
}

if (-not $SkipTests) {
    Write-Host ">> Running pytest -q -vv"
    & pytest -q -vv
}

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$outPath = Join-Path $SmokeDir ("smoke_report_{0}.json" -f $ts)
Write-Host ">> Running smoke pipeline (python) -> $outPath"
& python -u .\tools\smoke\smoke_pipeline.py -o $outPath

$lastPath = Join-Path $SmokeDir "last.json"
if (Test-Path $lastPath) { Remove-Item $lastPath -Force }
Copy-Item $outPath $lastPath
Write-Host "OK. Report saved:`n - $outPath`n - $lastPath"
Write-Host "=== Done ==="
