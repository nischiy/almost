param([string]$ProjectRoot = ".")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\stop_guard.ps1")
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\force_move_locked.ps1") -All
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\start_guard.ps1")
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\verify_tree.ps1") -Path (Join-Path $root "logs\health")
