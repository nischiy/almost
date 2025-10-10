param(
  [string]$ProjectRoot = ".",
  [string]$OutDir = "",
  [string]$NameSuffix = "release",
  [switch]$IncludeLogs = $false,
  [switch]$IncludeVenv = $false,
  [switch]$DryRun = $false,
  [switch]$NoManifest = $false,
  [string[]]$ExtraExclude = @()
)

Set-StrictMode -Off
$ErrorActionPreference = "Stop"

# -------- Resolve paths --------
$ROOT   = (Resolve-Path -LiteralPath $ProjectRoot).Path
$NAME   = Split-Path $ROOT -Leaf
$PARENT = Split-Path $ROOT -Parent

if ([string]::IsNullOrWhiteSpace($OutDir)) { $OutDir = $PARENT }
if (!(Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

$stamp   = Get-Date -Format "yyyyMMdd_HHmmss"
$OutFile = Join-Path $OutDir ("{0}_{1}_{2}.zip" -f $NAME, $NameSuffix, $stamp)
$Staging = Join-Path $OutDir ("_{0}_staging_{1}" -f $NAME, $stamp)

Write-Host ">>> ProjectRoot = $ROOT"
Write-Host ">>> OutFile     = $OutFile"
Write-Host ">>> Staging     = $Staging"

# -------- Exclusion rules (directories and files) --------
$DirExcludes = @(
  "\.git", "\.idea", "\.vscode", "node_modules",
  "__pycache__", "\.pytest_cache"
)
if (-not $IncludeVenv) { $DirExcludes += @("\.venv", "venv") }
if (-not $IncludeLogs) { $DirExcludes += @("\logs\") }

# Always exclude the staging and output names to avoid self-inclusion
$DirExcludes += @([System.IO.Path]::GetFileName($Staging))

$FileExcludeRegex = @(
  "\.pyc$", "\.pyo$", "\.log$", "\.tmp$", "\.bak(\.|$)",
  "\.DS_Store$", "Thumbs\.db$"
)

# Merge user extra excludes (treated as substrings for dirs and regex for files)
$UserDirEx = @()
$UserFileRe = @()
foreach ($x in $ExtraExclude) {
  if ($x -match "[\\/]" -or $x -match "^\..*") { $UserDirEx += $x.ToLowerInvariant() }
  else { $UserFileRe += $x }
}
$DirExcludes += $UserDirEx
$FileExcludeRegex += $UserFileRe

function Test-ExcludedPath([string]$full) {
  $p = $full.ToLowerInvariant()
  foreach ($mark in $DirExcludes) {
    if ([string]::IsNullOrWhiteSpace($mark)) { continue }
    if ($p -like "*$mark*") { return $true }
  }
  return $false
}
function Test-ExcludedFile([string]$name) {
  $n = $name.ToLowerInvariant()
  foreach ($re in $FileExcludeRegex) {
    if ([string]::IsNullOrWhiteSpace($re)) { continue }
    if ($n -match $re) { return $true }
  }
  return $false
}

# -------- Collect files under $ROOT deterministically --------
$allFiles = Get-ChildItem -LiteralPath $ROOT -Recurse -File -Force | Sort-Object FullName | Where-Object {
  -not (Test-ExcludedPath $_.DirectoryName) -and -not (Test-ExcludedFile $_.Name)
}

# Never include raw secrets (keep .env.example if present)
$allFiles = $allFiles | Where-Object { $_.Name -ne ".env" -and $_.Name -notmatch "^\.env\.(local|prod|dev|secrets?)$" }

if ($DryRun) {
  Write-Host "---- DRY RUN: files that would be included ----"
  foreach ($f in $allFiles) {
    $rel = $f.FullName.Substring($ROOT.Length).TrimStart('\','/')
    Write-Host $rel
  }
  Write-Host "---- DRY RUN END (count = $($allFiles.Count)) ----"
  return
}

# -------- Prepare staging --------
if (Test-Path -LiteralPath $Staging) { Remove-Item -LiteralPath $Staging -Recurse -Force }
New-Item -ItemType Directory -Path $Staging | Out-Null

# -------- Copy to staging, preserving hierarchy --------
$copied = 0
foreach ($f in $allFiles) {
  $rel = $f.FullName.Substring($ROOT.Length).TrimStart('\','/')
  $dest = Join-Path $Staging $rel
  $destDir = Split-Path $dest -Parent
  if (!(Test-Path -LiteralPath $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
  Copy-Item -LiteralPath $f.FullName -Destination $dest -Force
  $copied++
}

# -------- Emit manifest (optional, on by default) --------
if (-not $NoManifest) {
  $manifestPath = Join-Path $Staging "MANIFEST.json"
  $entries = @()
  $stageFiles = Get-ChildItem -LiteralPath $Staging -Recurse -File | Sort-Object FullName
  foreach ($sf in $stageFiles) {
    $rel = $sf.FullName.Substring($Staging.Length).TrimStart('\','/')
    $h = Get-FileHash -LiteralPath $sf.FullName -Algorithm SHA256
    $entries += [pscustomobject]@{
      path = ($rel -replace "\\","/")
      size = [int64]$sf.Length
      sha256 = $h.Hash.ToLowerInvariant()
    }
  }
  $payload = [pscustomobject]@{
    project = $NAME
    created_at = (Get-Date).ToString("s")
    files = $entries
  }
  $payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
}

# -------- Create ZIP from staging root --------
if (Test-Path -LiteralPath $OutFile) { Remove-Item -LiteralPath $OutFile -Force }
Compress-Archive -Path (Join-Path $Staging '*') -DestinationPath $OutFile -Force

# -------- Validate archive entry names (no backslashes) --------
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($OutFile)
$bad = @()
foreach ($e in $zip.Entries) {
  if ($e.FullName -match "\\\\") { $bad += $e.FullName }
}
$zip.Dispose()

if ($bad.Count -gt 0) {
  Write-Warning "Archive contains entries with backslashes in names (invalid structure):"
  $bad | ForEach-Object { Write-Warning "  $_" }
  throw "Invalid ZIP entry names detected. Aborting."
}

# -------- Cleanup staging --------
Remove-Item -LiteralPath $Staging -Recurse -Force

# -------- Summary --------
Write-Host "[DONE] Archive created ($copied files): $OutFile"
Write-Host "Exclusions (dirs): $($DirExcludes -join ', ')"
Write-Host "Exclusions (files regex): $($FileExcludeRegex -join ', ')"
