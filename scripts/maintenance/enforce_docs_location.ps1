param([string]$ProjectRoot = ".")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
$patterns = @("README*.md","README*.txt","PATCH*.md","PATCH*.txt","*NOTES*.txt","*RUNBOOK*.md","*CHECKLIST*.md","*SURPRISE_TOOLS*.md","*UPGRADE*_README*.md")
$viol = @()
foreach ($p in $patterns) {
    $viol += Get-ChildItem -Path (Join-Path $ROOT $p) -File -ErrorAction SilentlyContinue
}

if ($viol.Count -gt 0) {
    Write-Error ("README-like files found in project root. Move them to docs\\readmes:\n" + ($viol | ForEach-Object { " - " + $_.Name } | Out-String))
    exit 1
} else {
    Write-Host "[OK] No README-like files in project root."
}
