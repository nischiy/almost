param(
  [string]$ProjectRoot = "."
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host "=== Stop Guard (process mode) ==="
$runDir = Join-Path -Path $root -ChildPath "run"
$killPidFile   = Join-Path -Path $runDir -ChildPath "kill_switch.pid"
$healthPidFile = Join-Path -Path $runDir -ChildPath "health_loop.pid"
$flag = Join-Path -Path $root -ChildPath "run\STOP_GUARD.flag"
New-Item -ItemType File -Path $flag -Force | Out-Null

foreach ($pf in @($killPidFile, $healthPidFile)) {
  if (Test-Path -LiteralPath $pf) {
    try {
      $pid = [int](Get-Content -LiteralPath $pf | Select-Object -First 1)
      Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    } catch {}
    Remove-Item -LiteralPath $pf -Force -ErrorAction SilentlyContinue
  }
}
Write-Host "STOP_GUARD.flag created; processes signaled to stop."
