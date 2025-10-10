Param(
    [string]$ProjectRoot = "."
)

Write-Host ">>> Cleanup starting at: $ProjectRoot"

# 1) Remove duplicate single-file modules that conflict with packages
$dupFiles = @(
    "core\telemetry.py",
    "core\config.py",
    "core\risk.py"
)
foreach ($rel in $dupFiles) {
    $p = Join-Path $ProjectRoot $rel
    if (Test-Path $p) {
        Write-Host " - Removing duplicate file: $rel"
        Remove-Item -Force $p
    }
}

# 2) Drop caches/pyc
Get-ChildItem -Path $ProjectRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $ProjectRoot -Recurse -Filter *.pyc -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

# 3) Strip BOMs
$py = Join-Path $ProjectRoot "tools\strip_bom.py"
if (Test-Path $py) {
    Write-Host " - Stripping BOMs via tools\strip_bom.py ..."
    & python $py $ProjectRoot
} else {
    Write-Warning "tools\strip_bom.py not found; skipping BOM strip."
}

Write-Host ">>> Cleanup done."
