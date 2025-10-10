param(
  [string]$ProjectRoot = "."
)
Set-StrictMode -Off
$ErrorActionPreference = "Stop"

# Resolve project root and Python
$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
$PY = Join-Path $ROOT ".venv\Scripts\python.exe"
if (!(Test-Path $PY)) { $PY = "python" }

function Get-PyPkgVersion {
  param([Parameter(Mandatory=$true)][string]$Name)
  try {
    $out = & $PY -m pip show $Name 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $out) { return "" }
    foreach ($line in $out) {
      if ($line -like "Version:*") {
        return ($line -split ":\s*",2)[1].Trim()
      }
    }
    return ""
  } catch {
    return ""
  }
}

function Compare-Version {
  param([string]$A, [string]$B)
  if ([string]::IsNullOrWhiteSpace($A)) { return -1 }
  $pa = $A.Split('.'); $pb = $B.Split('.')
  $max = [Math]::Max($pa.Length, $pb.Length)
  for ($i=0; $i -lt $max; $i++) {
    $va = if ($i -lt $pa.Length) { [int]($pa[$i] -as [int]) } else { 0 }
    $vb = if ($i -lt $pb.Length) { [int]($pb[$i] -as [int]) } else { 0 }
    if ($va -gt $vb) { return 1 }
    if ($va -lt $vb) { return -1 }
  }
  return 0
}

function Ensure-Package {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][string]$MinVersion
  )
  $ver = Get-PyPkgVersion -Name $Name
  if ([string]::IsNullOrWhiteSpace($ver)) {
    Write-Host "Installing $Name>=$MinVersion ..."
    & $PY -m pip install "$Name>=$MinVersion" --upgrade
    return
  }
  $cmp = Compare-Version -A $ver -B $MinVersion
  if ($cmp -lt 0) {
    Write-Host "Upgrading $Name to >= $MinVersion (current $ver) ..."
    & $PY -m pip install "$Name>=$MinVersion" --upgrade
  } else {
    Write-Host "$Name OK ($ver)"
  }
}

Push-Location $ROOT
try {
  # Core dependencies (Windows-friendly)
  Ensure-Package -Name "python-binance" -MinVersion "1.0.19"
  Ensure-Package -Name "pandas"         -MinVersion "2.0.0"
  Ensure-Package -Name "numba"          -MinVersion "0.59.0"
  Ensure-Package -Name "ta"             -MinVersion "0.11.0"
  Ensure-Package -Name "pydantic"       -MinVersion "2.0.0"
  # Optional
  try { Ensure-Package -Name "orjson"   -MinVersion "3.9.0" } catch { Write-Warning "orjson optional" }

  # Run Python preflight (writes logs/preflight/YYYY-MM-DD/*.json)
  & $PY ".\scripts\preflight_all.py"
  if ($LASTEXITCODE -ne 0) { throw "preflight_all.py failed with exit code $LASTEXITCODE" }
  Write-Host "Preflight: OK"
} finally {
  Pop-Location
}
