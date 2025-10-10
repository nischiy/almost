param(
    [switch]$SkipTests
)
# Minimal, ASCII-only runner. Tested on Windows PowerShell 5+.
$ErrorActionPreference = "Stop"

# Resolve repo root (this file is scripts/paper/run_paper.ps1)
$repo = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $repo
Write-Host "=== Paper run (offline) ==="
Write-Host "Repo: $repo"

# 1) Preflight in Strict mode
Write-Host ">> Preflight (Strict)"
& "$repo\scripts\preflight.ps1" -Strict

# 2) Pytest (unless skipped)
if (-not $SkipTests) {
    Write-Host ">> Running pytest -q -vv"
    & pytest -q -vv
} else {
    Write-Host ">> Skipping tests by user request"
}

# 3) Run existing smoke pipeline to generate a JSON report
$smokePs1 = "$repo\scripts\smoke\run_smoke_pipeline.ps1"
if (Test-Path $smokePs1) {
    Write-Host ">> Running smoke pipeline"
    & $smokePs1
} else {
    Write-Warning "smoke pipeline script not found: $smokePs1"
}

# 4) Copy last report into logs/paper
$outDir = "$repo\logs\paper"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$lastSmoke = "$repo\logs\smoke\last.json"
if (Test-Path $lastSmoke) {
    Copy-Item $lastSmoke "$outDir\last.json" -Force
    Write-Host "OK. Report copied:"
    Write-Host " - $outDir\last.json"
} else {
    Write-Warning "No smoke report found at: $lastSmoke"
}

Write-Host "=== Done ==="
