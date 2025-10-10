# scripts/tools/safe_ops.ps1  (compat)
param(
    [Parameter(Position=0)][string]$Action,
    [Parameter(Position=1)][string]$Arg1,
    [Parameter(Position=2)][string]$Arg2,
    [Parameter(Position=3)][string]$Arg3
)
if (-not $Action) { $Action = "help" }
if ($null -eq $Arg1) { $Arg1 = "" }
if ($null -eq $Arg2) { $Arg2 = "" }
if ($null -eq $Arg3) { $Arg3 = "" }

function Run-Preflight {
    Write-Host "=== Preflight v2 (read-only) ==="
    $py = "$PWD\.venv\Scripts\python.exe"
    if (-not (Test-Path $py)) { $py = "python" }
    & $py "scripts/diagnostics/preflight_v2.py"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
function Rotate-Logs {
    param([string]$LogDir, [int]$MaxMb = 100, [int]$KeepDays = 14)
    if (-not $LogDir) { Write-Error "LogDir is required"; exit 2 }
    Write-Host "=== Log rotation === dir=$LogDir max_total_mb=$MaxMb keep_days=$KeepDays"
    $py = "$PWD\.venv\Scripts\python.exe"
    if (-not (Test-Path $py)) { $py = "python" }
    & $py -c "from utils.logrotate import rotate_logs; import json; print(json.dumps(rotate_logs(r'$LogDir', $MaxMb, $KeepDays), indent=2))"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
switch ($Action.ToLower()) {
  "preflight" { Run-Preflight }
  "rotate-logs" { Rotate-Logs -LogDir $Arg1 -MaxMb ([int]$Arg2) -KeepDays ([int]$Arg3) }
  default {
    Write-Host "Usage:"
    Write-Host "  safe_ops.ps1 preflight"
    Write-Host "  safe_ops.ps1 rotate-logs <log_dir> <max_total_mb> <keep_days>"
  }
}
