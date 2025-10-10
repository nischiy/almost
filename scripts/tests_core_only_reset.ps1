# scripts\tests_core_only_reset.ps1
# Deletes old test trees that could be auto-discovered and cause hangs.
$targets = @("tests", "tests_backup*", "tests_legacy*", "old_tests*", "archive_tests*")
foreach ($t in $targets) {
    Get-ChildItem -Path . -Filter $t -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "Removing $($_.FullName) ..." -ForegroundColor Yellow
        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "Done. Now run: pytest -q" -ForegroundColor Green
