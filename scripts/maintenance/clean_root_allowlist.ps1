param(
    [string]$ProjectRoot = ".",
    [switch]$WhatIf
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-ProjectPath([string]$root) { (Resolve-Path -LiteralPath $root).Path }
function Ensure-Dir([string]$p) { if (!(Test-Path $p)) { New-Item -ItemType Directory -Path $p | Out-Null } }

$ROOT = Resolve-ProjectPath $ProjectRoot
Write-Host ">>> ProjectRoot = $ROOT"
Write-Host ">>> WhatIf: $($WhatIf.IsPresent)"

# Allowlist for files that may remain in the ROOT
$keep = @(
    "main.py",
    ".env",
    ".env.example",
    "requirements.txt",
    "requirements.append.txt",
    "make_archive.ps1",
    "make_archive.bat"
)

# Ensure docs/readmes exists (for any notes)
$docs = Join-Path $ROOT "docs\readmes"
Ensure-Dir $docs

# 1) Move README/PATCH notes to docs\readmes
$notePatterns = @("README*.md","README*.txt","PATCH*.md","PATCH*.txt","*NOTES*.txt","*RUNBOOK*.md","*SURPRISE_TOOLS*.md","*UPGRADE*_README*.md","*RELEASE_CHECKLIST*.md","*UPDATE_NOTES*.txt")
foreach ($pat in $notePatterns) {
    Get-ChildItem -Path (Join-Path $ROOT $pat) -File -ErrorAction SilentlyContinue | ForEach-Object {
        $src = $_.FullName
        $dst = Join-Path $docs $_.Name
        if ($WhatIf) {
            Write-Host "[WhatIf] Move NOTE: $src -> $dst"
        } else {
            Move-Item -LiteralPath $src -Destination $dst -Force
            Write-Host "[MOVE] NOTE: $src -> $dst"
        }
    }
}

# 2) Remove stray files in ROOT that are not on allowlist
Get-ChildItem -Path $ROOT -File | ForEach-Object {
    $name = $_.Name
    if ($keep -contains $name) { return }
    # skip version control / hidden files entirely (handled as directories)
    if ($WhatIf) {
        Write-Host "[WhatIf] DELETE: $($_.FullName)"
    } else {
        Remove-Item -LiteralPath $_.FullName -Force
        Write-Host "[DEL] $($_.FullName)"
    }
}

Write-Host "[OK] Root contains only allowlisted files now."
