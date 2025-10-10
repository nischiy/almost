<# 
.cleanup_root.ps1
Purpose: Tidy the project ROOT by moving docs, env templates, and scripts to their folders
and deleting only safe junk files. Idempotent, with a Dry-Run mode.

USAGE (from project root):
  # Dry run (see actions only)
  powershell -ExecutionPolicy Bypass -File .\cleanup_root.ps1 -DryRun

  # Apply changes
  powershell -ExecutionPolicy Bypass -File .\cleanup_root.ps1
#>

param(
  [switch]$DryRun
)

function Write-Step($msg) { Write-Host "[CLEAN]" $msg }

# 0) Resolve project root = folder where this script lives
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
$Root = Get-Location

# 1) Dest folders
$DocsDir = Join-Path $Root "docs"
$ReadmesDir = Join-Path $DocsDir "readmes"
$OpsDir = Join-Path $DocsDir "ops"
$ConfigEnvDir = Join-Path $Root "config\env_templates"
$ScriptsDir = Join-Path $Root "scripts"

$dirs = @($DocsDir,$ReadmesDir,$OpsDir,$ConfigEnvDir,$ScriptsDir)
foreach($d in $dirs){ if(!(Test-Path $d)){ if($DryRun){ Write-Step "MKDIR $d" } else { New-Item -ItemType Directory -Force $d | Out-Null } } }

# 2) Move rules (root -> subfolders)
$moveRules = @(
  @{ Pattern = "README*.md";                   Dest = $ReadmesDir; Keep = @("README.md") },
  @{ Pattern = "*_README.md";                  Dest = $ReadmesDir; Keep = @() },
  @{ Pattern = "RUNBOOK*.md";                  Dest = $ReadmesDir; Keep = @() },
  @{ Pattern = "RELEASE_CHECKLIST.md";         Dest = $OpsDir;     Keep = @() },
  @{ Pattern = "README_RELEASE*.md";           Dest = $OpsDir;     Keep = @() },
  @{ Pattern = "UPGRADE_LIVE_CHECKS_README.md";Dest = $OpsDir;     Keep = @() },
  @{ Pattern = "PATCH*.md";                    Dest = $OpsDir;     Keep = @() },
  @{ Pattern = "PATCH*.txt";                   Dest = $OpsDir;     Keep = @() },
  @{ Pattern = "UPDATE*.txt";                  Dest = $OpsDir;     Keep = @() },
  @{ Pattern = ".env.*";                       Dest = $ConfigEnvDir;Keep = @(".env") },
  @{ Pattern = "run_tests.ps1";                Dest = $ScriptsDir; Keep = @() },
  @{ Pattern = "make_archive.ps1";             Dest = $ScriptsDir; Keep = @() },
  @{ Pattern = "make_archive.bat";             Dest = $ScriptsDir; Keep = @() },
  @{ Pattern = "run_fix.bat";                  Dest = $ScriptsDir; Keep = @() }
)

foreach($rule in $moveRules){
  $pattern = $rule.Pattern
  $dest = $rule.Dest
  $keep = $rule.Keep
  Get-ChildItem -File -Path $Root -Filter $pattern | ForEach-Object {
    if($keep -and $keep -contains $_.Name){ return }
    $to = Join-Path $dest $_.Name
    if($DryRun){
      Write-Step "MOVE $($_.Name) -> $((Resolve-Path $dest).Path)"
    } else {
      Move-Item -Force $_.FullName $to
    }
  }
}

# 3) Special case: root risk.py (archive to avoid import confusion)
$riskRoot = Join-Path $Root "risk.py"
$dstRisk = Join-Path $Root "core\risk\misc_risk_root.py"
if(Test-Path $riskRoot){
  if($DryRun){
    Write-Step "MOVE risk.py -> core/risk/misc_risk_root.py"
  } else {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dstRisk) | Out-Null
    Move-Item -Force $riskRoot $dstRisk
  }
}

# 4) Delete only obvious junk (safe)
$junkPatterns = @(
  "*.bak", "*.bak_*", "*.tmp", "*.swp",
  ".DS_Store", "Thumbs.db",
  "*_IMPORT_SHIM.txt", ".gitkeep", ".keep"
)
foreach($pat in $junkPatterns){
  Get-ChildItem -File -Path $Root -Filter $pat | ForEach-Object {
    if($DryRun){ Write-Step "DEL  $($_.Name)" } else { Remove-Item -Force $_.FullName }
  }
}

# 5) Summary
Write-Step ("DONE " + ($(if($DryRun){"(dry-run: no changes applied)"}else{"(applied)"})))
