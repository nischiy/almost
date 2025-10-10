param(
  [string]$Symbols = "BTCUSDT,ETHUSDT,SOLUSDT",
  [string]$Intervals = "15m,1h,4h",
  [int]$Limit = 1000,
  [string]$OutDir = ""
)

$repo = (Resolve-Path ".").Path
$pyScript = Join-Path $repo "tmp\quick_sweep.py"
if (-not (Test-Path $pyScript)) { throw "Missing file: $pyScript" }

$pythonExe = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) { $pythonExe = "python" }

if (-not $OutDir) { $OutDir = Join-Path $repo "logs\diagnostics" }
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }

$argList = @($pyScript, "--symbols", $Symbols, "--intervals", $Intervals, "--limit", $Limit, "--outdir", $OutDir)
Write-Host (">> " + $pythonExe + " " + ($argList -join " "))
& $pythonExe @argList
exit $LASTEXITCODE
