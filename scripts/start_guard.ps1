param(
  [string]$ProjectRoot = "."
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host "=== Start Guard (as processes) ==="
Write-Host "ProjectRoot = $root"

$py = Join-Path -Path $root -ChildPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) { $py = "python" }

$runDir = Join-Path -Path $root -ChildPath "run"
$healthRoot = Join-Path -Path $root -ChildPath "logs\health"
$healthDir  = Join-Path -Path $healthRoot -ChildPath "guard"
New-Item -ItemType Directory -Path $runDir -Force    | Out-Null
New-Item -ItemType Directory -Path $healthRoot -Force| Out-Null
New-Item -ItemType Directory -Path $healthDir -Force | Out-Null

# pre-start cleanup: move any leftover files in health root into guard
Get-ChildItem -LiteralPath $healthRoot -File -ErrorAction SilentlyContinue | Where-Object {
  $_.Name -match '\.(log|json|jsonl)$'
} | ForEach-Object {
  try {
    Move-Item -LiteralPath $_.FullName -Destination (Join-Path -Path $healthDir -ChildPath $_.Name) -Force
  } catch {
    Start-Sleep -Milliseconds 150
    try { Move-Item -LiteralPath $_.FullName -Destination (Join-Path -Path $healthDir -ChildPath $_.Name) -Force } catch {}
  }
}

# remove STOP flag
$stopFlag = Join-Path -Path $root -ChildPath "run\STOP_GUARD.flag"
if (Test-Path -LiteralPath $stopFlag) { Remove-Item -LiteralPath $stopFlag -Force }

$killScript   = Join-Path -Path $root -ChildPath "tools\guard\kill_switch.py"
$healthScript = Join-Path -Path $root -ChildPath "tools\health\health_loop.py"

# separate logs for stdout and stderr (under logs/health/guard)
$killOutLog   = Join-Path -Path $healthDir -ChildPath "kill_switch.stdout.log"
$killErrLog   = Join-Path -Path $healthDir -ChildPath "kill_switch.stderr.log"
$healthOutLog = Join-Path -Path $healthDir -ChildPath "health_loop.stdout.log"
$healthErrLog = Join-Path -Path $healthDir -ChildPath "health_loop.stderr.log"

$killPidFile   = Join-Path -Path $runDir -ChildPath "kill_switch.pid"
$healthPidFile = Join-Path -Path $runDir -ChildPath "health_loop.pid"

# Start processes with redirected stdout/stderr (overwrite logs on each start)
$killProc = Start-Process -FilePath $py -ArgumentList "`"$killScript`"" -WorkingDirectory $root -PassThru -WindowStyle Hidden -RedirectStandardOutput $killOutLog -RedirectStandardError $killErrLog
$healthProc = Start-Process -FilePath $py -ArgumentList "`"$healthScript`"" -WorkingDirectory $root -PassThru -WindowStyle Hidden -RedirectStandardOutput $healthOutLog -RedirectStandardError $healthErrLog

$killProc.Id   | Out-File -LiteralPath $killPidFile   -Encoding ascii -Force
$healthProc.Id | Out-File -LiteralPath $healthPidFile -Encoding ascii -Force

Write-Host ("Started: kill_switch PID={0}, health_loop PID={1}" -f $killProc.Id, $healthProc.Id)
Write-Host ("Logs: `n  {0}`n  {1}`n  {2}`n  {3}" -f $killOutLog, $killErrLog, $healthOutLog, $healthErrLog)
