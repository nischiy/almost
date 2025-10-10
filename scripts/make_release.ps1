
<# make_release.ps1
Creates a clean ZIP archive of the project (production-ready), excluding junk.
Run from project root (where main.py is):
  powershell -ExecutionPolicy Bypass -File .\make_release.ps1

Optional flags:
  -IncludeTests    -> include ./tests folder
  -Name MyBuild    -> sets archive name prefix (default: release)
#>

param(
  [switch]$IncludeTests = $false,
  [string]$Name = "release"
)

$ErrorActionPreference = "Stop"
$root = Get-Location
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $root "dist"
$zipPath = Join-Path $outDir "$Name`_$ts.zip"

if(!(Test-Path $outDir)){ New-Item -ItemType Directory -Path $outDir | Out-Null }

# Collect include list (relative paths)
$include = @(
  "app",
  "core",
  "config",
  "models",
  "scripts",
  "requirements.txt",
  "requirements.append.txt",
  "pytest.ini",
  "README.md",
  "main.py"
)

if ($IncludeTests) { $include += "tests" }

# Exclude globs
$exclude = @(
  ".venv", "venv", "env", "dist", "build",
  ".git", ".github", ".idea", ".vscode",
  "__pycache__", "*.pyc", "*.pyo", "*.pyd",
  "logs", "tmp", "cache", "*.bak", "*.tmp", "Thumbs.db", ".DS_Store"
)

function Should-Exclude([string]$path){
  foreach($pat in $exclude){
    if ($path -like "*\$pat*") { return $true }
  }
  return $false
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

[System.IO.Compression.ZipArchiveMode] $mode = [System.IO.Compression.ZipArchiveMode]::Create
$fs = [System.IO.File]::Open($zipPath, [System.IO.FileMode]::Create)
$zip = New-Object System.IO.Compression.ZipArchive($fs, $mode)

foreach($rel in $include){
  $full = Join-Path $root $rel
  if(Test-Path $full){
    if((Get-Item $full).PSIsContainer){
      Get-ChildItem -Recurse -File $full | ForEach-Object {
        $p = $_.FullName
        if (-not (Should-Exclude $p)){
          $entryName = Resolve-Path -Relative $p
          [void]$zip.CreateEntryFromFile($p, $entryName, [System.IO.Compression.CompressionLevel]::Optimal)
        }
      }
    } else {
      if (-not (Should-Exclude $full)){
        $entryName = Resolve-Path -Relative $full
        [void]$zip.CreateEntryFromFile($full, $entryName, [System.IO.Compression.CompressionLevel]::Optimal)
      }
    }
  }
}

$zip.Dispose()
$fs.Dispose()

Write-Host "[PACK] Created: $zipPath"
