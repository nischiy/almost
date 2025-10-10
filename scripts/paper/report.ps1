param(
    [string]$JsonPath = ""
)
$ErrorActionPreference = "Stop"
$PSDefaultParameterValues['Out-File:Encoding']='utf8'

Write-Host "=== Paper report ==="
$repo = (Resolve-Path ".").Path
Write-Host "Repo: $repo"

# pick python
$venvPy = Join-Path $repo ".venv\Scripts\python.exe"
if (Test-Path $venvPy) { $python = $venvPy } else { $python = "python" }

# find input json
if (-not $JsonPath) {
    $JsonPath = Join-Path $repo "logs\paper\last.json"
    if (-not (Test-Path $JsonPath)) {
        $JsonPath = Join-Path $repo "logs\smoke\last.json"
    }
}
if (-not (Test-Path $JsonPath)) {
    throw "Не знайдено last.json (ані logs\paper\last.json, ані logs\smoke\last.json). Спочатку запусти .\scripts\paper\run_paper.ps1"
}

$mdOut = Join-Path $repo "logs\paper\last.md"
$txtOut = Join-Path $repo "logs\paper\last_summary.txt"
New-Item -ItemType Directory -Force -Path (Split-Path $mdOut) | Out-Null

& $python (Join-Path $repo "tools\paper\report_to_md.py") --input $JsonPath --md $mdOut --summary $txtOut

Write-Host "OK. Report saved:"
Write-Host " - $mdOut"
Write-Host " - $txtOut"