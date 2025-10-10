param(
  [switch]$Tail = $false,
  [int]$Last = 50
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path ".").Path
$runDir = Join-Path -Path $root -ChildPath "run"
$healthDir = Join-Path -Path $root -ChildPath "logs\health\guard"

$killOutLog   = Join-Path -Path $healthDir -ChildPath "kill_switch.stdout.log"
$killErrLog   = Join-Path -Path $healthDir -ChildPath "kill_switch.stderr.log"
$healthOutLog = Join-Path -Path $healthDir -ChildPath "health_loop.stdout.log"
$healthErrLog = Join-Path -Path $healthDir -ChildPath "health_loop.stderr.log"

$killPidFile   = Join-Path -Path $runDir -ChildPath "kill_switch.pid"
$healthPidFile = Join-Path -Path $runDir -ChildPath "health_loop.pid"

function Get-ProcState([Nullable[Int32]]$procId) {
  if ($procId -eq $null) { return "N/A" }
  try {
    $p = Get-Process -Id $procId -ErrorAction Stop
    return ("Running ({0})" -f $p.ProcessName)
  } catch {
    return "Not running"
  }
}

# Read PIDs if files exist
$killProcId = $null
if (Test-Path -LiteralPath $killPidFile) {
  try { $killProcId = [int](Get-Content -LiteralPath $killPidFile | Select-Object -First 1) } catch {}
}
$healthProcId = $null
if (Test-Path -LiteralPath $healthPidFile) {
  try { $healthProcId = [int](Get-Content -LiteralPath $healthPidFile | Select-Object -First 1) } catch {}
}

# Display-friendly PIDs
if ($killProcId -ne $null) { $killPidDisp = $killProcId.ToString() } else { $killPidDisp = "-" }
if ($healthProcId -ne $null) { $healthPidDisp = $healthProcId.ToString() } else { $healthPidDisp = "-" }

Write-Host "=== Guard Status (process mode) ==="
Write-Host ("kill_switch : PID={0}  State={1}" -f $killPidDisp, (Get-ProcState $killProcId))
Write-Host ("health_loop : PID={0}  State={1}" -f $healthPidDisp, (Get-ProcState $healthProcId))

Write-Host "`n--- Last $Last lines (kill: stdout) ---"
if (Test-Path -LiteralPath $killOutLog) { Get-Content -Tail $Last -Path $killOutLog } else { Write-Host "(no file yet)" }
Write-Host "`n--- Last $Last lines (kill: stderr) ---"
if (Test-Path -LiteralPath $killErrLog) { Get-Content -Tail $Last -Path $killErrLog } else { Write-Host "(no file yet)" }

Write-Host "`n--- Last $Last lines (health: stdout) ---"
if (Test-Path -LiteralPath $healthOutLog) { Get-Content -Tail $Last -Path $healthOutLog } else { Write-Host "(no file yet)" }
Write-Host "`n--- Last $Last lines (health: stderr) ---"
if (Test-Path -LiteralPath $healthErrLog) { Get-Content -Tail $Last -Path $healthErrLog } else { Write-Host "(no file yet)" }

if ($Tail) {
  Write-Host "`n=== Tail health stdout (Ctrl+C to stop) ==="
  if (Test-Path -LiteralPath $healthOutLog) { Get-Content $healthOutLog -Wait -ErrorAction SilentlyContinue } else { Write-Host "(no file yet)" }
}
