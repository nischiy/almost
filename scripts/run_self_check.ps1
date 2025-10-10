param(
    [string]$TestFile = "tests\\self_check_cfg_attrs.py"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Resolve-Path (Join-Path $root "..")
Push-Location $proj
try {
    if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }
    $log = Join-Path "logs" "self_check_cfg_attrs.txt"
    Write-Host "=== Running pytest $TestFile ==="
    pytest -q $TestFile 2>&1 | Tee-Object -FilePath $log
    Write-Host "=== Done. Log saved to $log ==="
} finally {
    Pop-Location
}
