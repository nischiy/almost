param(
    [string]$Symbol = "BTCUSDT",
    [string]$Interval = "1m",
    [int]$Days = 14,
    [int]$Trials = 1000,
    [string]$Workers = "auto",
    [string]$Python = ".\.venv\Scripts\python.exe",
    [string]$LogDir = "logs\autotune"
)

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Resolve worker count
$cpu = [Environment]::ProcessorCount
$w = if ($Workers -eq "auto") { [Math]::Max(1, [int]($cpu * 0.75)) } else { [int]$Workers }

Write-Host "[AUTO] CPU=$cpu | Workers=$w"
$jobs = @()

for ($i = 1; $i -le $w; $i++) {
    $log = Join-Path $LogDir ("tune_{0:00}.log" -f $i)
    $args = @("scripts\tune.py", "--symbol", $Symbol, "--interval", $Interval, "--days", $Days, "--n_iter", $Trials, "--worker_id", $i)
    Write-Host ("[AUTO] Spawn #$($i): {0} {1} -> {2}" -f $Python, ($args -join ' '), $log)

    $p = Start-Process -FilePath $Python -ArgumentList $args -NoNewWindow -RedirectStandardOutput $log -RedirectStandardError $log -PassThru
    $jobs += $p
}

Write-Host "[AUTO] Waiting for workers..."
$jobs | ForEach-Object { $_.WaitForExit() }
Write-Host "[AUTO] Done."
