$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Resolve-Path (Join-Path $root "..")
Push-Location $proj
try {
    if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }
    $log = Join-Path "logs" "self_check_core_cfg.txt"
    Write-Host "=== Running pytest tests\\self_check_core_cfg.py ==="
    pytest -q tests\\self_check_core_cfg.py 2>&1 | Tee-Object -FilePath $log
    Write-Host "=== Done. Log saved to $log ==="
} finally {
    Pop-Location
}
