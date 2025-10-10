# ASCII-only viewer for last paper report
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..").Path
$last = "$repo\logs\paper\last.json"
if (Test-Path $last) {
    Write-Host "/"
    Get-Content $last -Raw
} else {
    Write-Warning "logs\paper\last.json not found. Run scripts\paper\run_paper.ps1 first."
}
