param([string]$ProjectRoot = ".")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
$dst = Join-Path $ROOT "docs\readmes"
if (!(Test-Path $dst)) { New-Item -ItemType Directory -Path $dst | Out-Null }

$patterns = @("README*.md","README*.txt","PATCH*.md","PATCH*.txt","*NOTES*.txt","*RUNBOOK*.md","*CHECKLIST*.md","*SURPRISE_TOOLS*.md","*UPGRADE*_README*.md")
$moved = 0
foreach ($pat in $patterns) {
    Get-ChildItem -Path (Join-Path $ROOT $pat) -File -ErrorAction SilentlyContinue | ForEach-Object {
        $src = $_.FullName
        $dstFile = Join-Path $dst $_.Name
        Move-Item -LiteralPath $src -Destination $dstFile -Force
        Write-Host "[MOVE] $src -> $dstFile"
        $moved++
    }
}
Write-Host "[DONE] Moved $moved file(s)."
