[CmdletBinding()]
param(
    [switch]$Fast = $false
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$runner = Join-Path $repoRoot "scripts\smoke\run_smoke_pipeline.ps1"

if ($Fast) {
    & $runner -SkipPreflight -SkipTests
} else {
    & $runner
}
