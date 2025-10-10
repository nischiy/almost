param([string]$ProjectRoot = ".")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\stop_guard.ps1")
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\clean_health_root.ps1") -Aggressive
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\start_guard.ps1")
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\guard_status.ps1")
