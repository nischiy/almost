param(
  [string]$K = ""
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Always run from repo root (parent of scripts\)
$RepoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $RepoRoot

# Prefer venv python if present (compatible with older PowerShell - no ternary)
$venvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
  $py = $venvPy
} else {
  $py = "python"
}

$argsList = @("-m","pytest","-q")
if ($K -and $K.Trim().Length -gt 0) {
  $argsList += @("-k", $K)
}

& $py @argsList
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
