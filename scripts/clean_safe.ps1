Param(
  [string]$Report = ".\logs\cleanup_report.json",
  [switch]$DeleteUnreachable = $false,
  [switch]$DeleteBackups = $false,
  [switch]$DeletePycache = $false
)

if (-not (Test-Path $Report)) {
  Write-Host "[ERR] Report not found: $Report" -ForegroundColor Red
  exit 1
}

$reportObj = Get-Content $Report | ConvertFrom-Json
$root = (Get-Location).Path

Write-Host "=== Cleanup plan (dry-run by default) ===" -ForegroundColor Cyan
Write-Host "Entry modules:"
$reportObj.entry_modules | ForEach-Object { Write-Host "  - $_" }

Write-Host "`nUnreachable modules:"
$reportObj.unreachable_modules | ForEach-Object { Write-Host "  - $_" }

Write-Host "`nBackup files (*.bak_*):"
$reportObj.backup_files | ForEach-Object { Write-Host "  - $_" }

Write-Host "`nPycache dirs:"
$reportObj.pycache_dirs | ForEach-Object { Write-Host "  - $_" }

if ($DeleteUnreachable) {
  Write-Host "`n[Action] Deleting unreachable modules..." -ForegroundColor Yellow
  foreach ($m in $reportObj.unreachable_modules) {
    $path1 = ($m -replace '\.', '\') + ".py"
    $path2 = ($m -replace '\.', '\') + "\__init__.py"
    $full1 = Join-Path $root $path1
    $full2 = Join-Path $root $path2
    if (Test-Path $full1) { Remove-Item $full1 -Force -ErrorAction SilentlyContinue }
    if (Test-Path $full2) { Remove-Item $full2 -Force -ErrorAction SilentlyContinue }
  }
}

if ($DeleteBackups) {
  Write-Host "`n[Action] Deleting backup files..." -ForegroundColor Yellow
  $reportObj.backup_files | ForEach-Object {
    if (Test-Path $_) { Remove-Item $_ -Force -ErrorAction SilentlyContinue }
  }
}

if ($DeletePycache) {
  Write-Host "`n[Action] Deleting __pycache__ dirs..." -ForegroundColor Yellow
  $reportObj.pycache_dirs | ForEach-Object {
    if (Test-Path $_) { Remove-Item $_ -Recurse -Force -ErrorAction SilentlyContinue }
  }
}

Write-Host "`nDone." -ForegroundColor Green
