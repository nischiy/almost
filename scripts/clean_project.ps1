
<#  scripts/clean_project.ps1  (fixed)
    Безпечно чистить проект: кеші, тимчасові файли, підозрілі дублікати.
    DRY-RUN за замовчуванням. Для видалення додай -Delete.
#>

param(
  [switch]$Delete = $false,
  [switch]$PruneLogs = $false,
  [int]$KeepLogDays = 14
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---- Навігація до кореня проєкту ----
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $root

Write-Host "Project root:" (Get-Location) -ForegroundColor Cyan
$removed = @()
$skipped = @()

# ---- Налаштування ----
$ignoreDirs = @(".git", ".svn", ".hg", ".venv", "venv", "node_modules", ".idea", ".vscode")
$protectedDirs = @("models", "logs")
$alwaysRemoveDirs = @("__pycache__", ".pytest_cache", ".ipynb_checkpoints")
$alwaysRemoveFiles = @("Thumbs.db", ".DS_Store", ".AppleDouble")
$junkGlobs = @("*.pyc", "*.pyo", "*.orig", "*.rej", "*~", "*.bak", "*.tmp")
$shadowNamePatterns = @(
  "* - Copy.*", "* (copy).*", "* (копия).*", "* (копія).*",
  "* (1).*", "* (2).*", "* (old).*", "*_old.*", "*_backup.*", "*backup*.*", "*_prev.*"
)
$dupScanIncludeDirs = @("app","core","strategies","scripts","tests")
$dupScanExcludeDirs = $ignoreDirs + $protectedDirs + $alwaysRemoveDirs

function In-AnyDir([string]$path, [string[]]$dirs) {
  foreach ($d in $dirs) {
    # match directory segment
    if ($path -like ("*\{0}\*" -f $d)) { return $true }
    # compare last path segment explicitly to avoid parser confusion
    $leaf = Split-Path -Path $path -Leaf
    if ($leaf -ieq $d) { return $true }
  }
  return $false
}

function SafeRemove($item) {
  if ($Delete) {
    Remove-Item -LiteralPath $item -Force -Recurse -ErrorAction SilentlyContinue
    $script:removed += $item
  } else {
    Write-Host "[DRY-RUN] would remove -> $item" -ForegroundColor Yellow
  }
}

# ---- Крок 1: прибрати кеші та сміття ----
Write-Host "`n[1/4] Cleaning caches & junk..." -ForegroundColor Green
foreach ($d in $alwaysRemoveDirs) {
  Get-ChildItem -Recurse -Directory -Filter $d -ErrorAction SilentlyContinue |
    ForEach-Object {
      if (-not (In-AnyDir $_.FullName $ignoreDirs)) { SafeRemove $_.FullName }
    }
}
foreach ($g in $junkGlobs) {
  Get-ChildItem -Recurse -File -Filter $g -ErrorAction SilentlyContinue |
    Where-Object { -not (In-AnyDir $_.FullName $ignoreDirs) } |
    ForEach-Object { SafeRemove $_.FullName }
}
foreach ($f in $alwaysRemoveFiles) {
  Get-ChildItem -Recurse -File -Filter $f -ErrorAction SilentlyContinue |
    ForEach-Object { SafeRemove $_.FullName }
}

# ---- Крок 2: «тіньові» копії ----
Write-Host "`n[2/4] Detecting shadow/duplicate-named files..." -ForegroundColor Green
foreach ($pat in $shadowNamePatterns) {
  Get-ChildItem -Recurse -File -Filter $pat -ErrorAction SilentlyContinue |
    Where-Object { -not (In-AnyDir $_.FullName $ignoreDirs) } |
    ForEach-Object {
      if (In-AnyDir $_.FullName $protectedDirs) { $script:skipped += $_.FullName }
      else { SafeRemove $_.FullName }
    }
}

# ---- Крок 3: точні дублі (MD5) ----
Write-Host "`n[3/4] Scanning for exact duplicate files (by MD5)..." -ForegroundColor Green
$dupCandidates = @()
foreach ($dir in $dupScanIncludeDirs) {
  if (Test-Path $dir) {
    $dupCandidates += Get-ChildItem -Path $dir -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object { -not (In-AnyDir $_.FullName $dupScanExcludeDirs) }
  }
}
$hashGroups = @{}
foreach ($f in $dupCandidates) {
  try {
    $h = (Get-FileHash -LiteralPath $f.FullName -Algorithm MD5).Hash
    if (-not $hashGroups.ContainsKey($h)) { $hashGroups[$h] = @() }
    $hashGroups[$h] += $f.FullName
  } catch { }
}
foreach ($pair in $hashGroups.GetEnumerator()) {
  $files = $pair.Value
  if ($files.Count -gt 1) {
    Write-Host "  Duplicate group:" -ForegroundColor Magenta
    $files | ForEach-Object { Write-Host "    $_" }
    $keep = $files | Sort-Object { $_.Length } | Select-Object -First 1
    foreach ($f in $files) {
      if ($f -ne $keep) { SafeRemove $f }
    }
  }
}

# ---- Крок 4: опційно чистити старі логи ----
if ($PruneLogs -and (Test-Path "logs")) {
  Write-Host "`n[4/4] Pruning logs older than $KeepLogDays days..." -ForegroundColor Green
  $threshold = (Get-Date).AddDays(-1 * $KeepLogDays)
  Get-ChildItem -Recurse -File "logs" -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $threshold } |
    ForEach-Object { SafeRemove $_.FullName }
} else {
  Write-Host "`n[4/4] Skip logs pruning (use -PruneLogs to enable)" -ForegroundColor DarkYellow
}

# ---- Підсумок ----
Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host ("  Removed (or would remove): {0}" -f $removed.Count)
Write-Host ("  Skipped (protected/ignored): {0}" -f $skipped.Count)
Write-Host ("  Duplicate groups processed: {0}" -f ($hashGroups.Values | Where-Object { $_.Count -gt 1 } | Measure-Object).Count)
if (-not $Delete) {
  Write-Host "`nDRY-RUN mode." -ForegroundColor Yellow
  Write-Host "If the plan looks good, rerun with:  .\scripts\clean_project.ps1 -Delete"
}
