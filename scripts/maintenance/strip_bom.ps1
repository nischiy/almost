param(
  [string]$Root = ".",
  [switch]$Check = $false,
  [switch]$Write = $false
)
# Windows PowerShell 5.1–compatible (без тернарного ?:)
if (($Check -and $Write) -or (-not $Check -and -not $Write)) {
  Write-Error "Specify exactly one: -Check or -Write"
  exit 2
}
$ErrorActionPreference="Stop"

# Спроба використати Python із .venv, інакше — системний
$resolvedRoot = (Resolve-Path $Root).Path
$py = Join-Path $resolvedRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

# Формуємо аргументи без тернарного оператора
$argsList = @("--root", $resolvedRoot)
if ($Check) { $argsList += "--check" } else { $argsList += "--write" }

& $py "scripts/maintenance/strip_bom.py" @argsList
exit $LASTEXITCODE
