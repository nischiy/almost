# scripts\replace_tests_with_core.ps1
Param([string]$ZipPath = ".\withouttrah_tests_fresh_core_v1.zip")

Write-Host ">>> Backing up existing tests\ to tests_backup_* ..." -ForegroundColor Cyan
$Backup = "tests_backup_{0:yyyyMMdd_HHmmss}" -f (Get-Date)
if (Test-Path .\tests) { Copy-Item .\tests $Backup -Recurse -Force }

Write-Host ">>> Removing tests\ ..." -ForegroundColor Cyan
if (Test-Path .\tests) { Remove-Item .\tests -Recurse -Force }

Write-Host ">>> Extracting fresh core-only tests ..." -ForegroundColor Cyan
Expand-Archive -LiteralPath $ZipPath -DestinationPath . -Force

Write-Host ">>> Done. Run:  pytest -q" -ForegroundColor Green
