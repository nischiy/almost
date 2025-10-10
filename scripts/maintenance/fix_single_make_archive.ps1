param(
  [string]$ProjectRoot = ".",
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-Log {
  param([string]$Message)
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  "$stamp  $Message" | Tee-Object -FilePath $Global:LogFile -Append
}

function Ensure-Dir([string]$Path) {
  if (!(Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null }
}

# 0) Resolve paths and init logs
$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
$TRASH = Join-Path $ROOT ".trash"
$BACKUP = Join-Path $TRASH ("removed_make_archive_{0}" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
$LOGDIR = Join-Path $ROOT "logs\maintenance"
Ensure-Dir $TRASH
Ensure-Dir $BACKUP
Ensure-Dir $LOGDIR
$Global:LogFile = Join-Path $LOGDIR ("fix_single_make_archive_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Log "ProjectRoot: $ROOT"

# 1) Canonical target must exist
$Canonical = Join-Path $ROOT "make_archive.ps1"
if (!(Test-Path -LiteralPath $Canonical)) {
  throw "Canonical file not found: $Canonical"
}
New-Log "Canonical: $Canonical"

# 2) Build duplicate list (fixed: no stray commas inside Join-Path)
$Cand1 = Join-Path $ROOT "make_archive.ps1"
$Cand2 = Join-Path $ROOT "make_archive.ps1"
$Candidates = @()
if (Test-Path -LiteralPath $Cand1) { $Candidates += $Cand1 }
if (Test-Path -LiteralPath $Cand2) { $Candidates += $Cand2 }

if ($Candidates.Count -eq 0) {
  New-Log "No duplicate make_archive.ps1 found. Nothing to remove."
} else {
  foreach ($dup in $Candidates) {
    New-Log "Duplicate found: $dup"
    if ($DryRun) {
      New-Log "[DRY] Would move '$dup' -> '$BACKUP'"
    } else {
      Ensure-Dir $BACKUP
      $rel = $dup.Substring($ROOT.Length).TrimStart("\","/")
      $target = Join-Path $BACKUP ($rel -replace "[/\\]", "_")
      Move-Item -LiteralPath $dup -Destination $target
      New-Log "Moved duplicate to backup: $target"
    }
  }
}

# 3) Replace references across the repo
$Patterns = @(
  'scripts[\\/]+make_archive\.ps1',
  'scripts[\\/]+release[\\/]+make_archive\.ps1'
)
$Extensions = @("*.ps1","*.psm1","*.psd1","*.py","*.md","*.txt","*.yml","*.yaml","*.ini","*.cfg","*.toml",".editorconfig",".gitattributes",".gitignore")
$Files = @()
foreach ($ext in $Extensions) {
  try {
    $Files += Get-ChildItem -LiteralPath $ROOT -Recurse -File -Filter $ext -ErrorAction Stop
  } catch {
    # Some extensions like dotfiles won't match via -Filter; add a fallback scan
    if ($ext -like ".*") {
      $Files += Get-ChildItem -LiteralPath $ROOT -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq $ext }
    }
  }
}

$TotalRewrites = 0
foreach ($file in $Files) {
  try {
    $content = [System.IO.File]::ReadAllText($file.FullName)
  } catch {
    continue
  }
  $orig = $content
  foreach ($pat in $Patterns) {
    $content = [System.Text.RegularExpressions.Regex]::Replace($content, $pat, 'make_archive.ps1')
  }
  if ($content -ne $orig) {
    $TotalRewrites++
    if ($DryRun) {
      New-Log ("[DRY] Would rewrite references in: {0}" -f $file.FullName)
    } else {
      $relpath = $file.FullName.Substring($ROOT.Length).TrimStart("\","/")
      $bk = Join-Path $BACKUP ($relpath -replace "[/\\]", "_")
      Copy-Item -LiteralPath $file.FullName -Destination $bk -Force
      [System.IO.File]::WriteAllText($file.FullName, $content, (New-Object System.Text.UTF8Encoding($false)))
      New-Log ("Rewrote references in: {0}" -f $file.FullName)
    }
  }
}

New-Log ("Reference rewrites: {0}" -f $TotalRewrites)

# 4) Verify result
$StillDup = @()
if (Test-Path -LiteralPath $Cand1) { $StillDup += $Cand1 }
if (Test-Path -LiteralPath $Cand2) { $StillDup += $Cand2 }

if ($StillDup.Count -gt 0) {
  $list = ($StillDup -join ", ")
  if ($DryRun) {
    New-Log "[DRY] Duplicates would remain (DryRun): $list"
  } else {
    throw "Some duplicates still present: $list"
  }
} else {
  New-Log "No duplicates remain. Canonical file is only: $Canonical"
}

New-Log "Done."