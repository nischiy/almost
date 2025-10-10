param(
    [string]$Symbol = "BTCUSDT",
    [string]$BaseUrl = "",
    [switch]$Quiet
)

# Resolve repo root and script path
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$pyScript = Join-Path $repoRoot "tools\live\ping_exchange.py"

if (-not (Test-Path $pyScript)) {
    Write-Error ("Missing file: {0}. Expected at tools\live\ping_exchange.py" -f $pyScript)
    exit 2
}

# Prefer venv python, fallback to system python
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

$env:PYTHONIOENCODING = "utf-8"

# Build args
$argsList = @($pyScript)
if ($Symbol) { $argsList += @("--symbol", $Symbol) }
if ($BaseUrl) { $argsList += @("--base-url", $BaseUrl) }

# Run and measure
$sw = [System.Diagnostics.Stopwatch]::StartNew()
& $python @argsList
$code = $LASTEXITCODE
$sw.Stop()

if (-not $Quiet) {
    Write-Host ("ExitCode={0} TimeMs={1}" -f $code, $sw.ElapsedMilliseconds)
}

exit $code
