param(
  [string]$ProjectRoot = "."
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
Write-Host "=== Fix Preflight Now ==="
Write-Host "ProjectRoot = $root"

$py = Join-Path -Path $root -ChildPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) { $py = "python" }

# 1) Install deps
$pkgs_critical = @("pydantic>=2.7")
$pkgs_optional = @("ta","numba","orjson")
foreach ($p in $pkgs_critical) {
  & $py -m pip install --upgrade $p
  if ($LASTEXITCODE -ne 0) { throw "Failed to install $p" }
}
foreach ($p in $pkgs_optional) {
  & $py -m pip install --upgrade $p 2>$null | Out-Null
}

# 2) Ensure risk keys in .env
& powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\ensure_env_risk_defaults.ps1")

# 3) Run preflight
& powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\preflight_all.ps1")
$code = $LASTEXITCODE
if ($code -ne 0) { exit $code }
