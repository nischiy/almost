<#
  Finalize cleanup: strip special comments and remove temporary patch scripts.
  Usage:
    powershell -ExecutionPolicy Bypass -File .\scripts\finalize_paper_csv_cleanup.ps1
#>
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $here "..")
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
if (Test-Path $venvPy) { $Python = $venvPy } else { $Python = "python" }

Write-Host ">>> Stripping special comments..."
& $Python ".\scripts\strip_disabled_paper_lines.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$junk = @(
    "scripts\apply_paper_patch.ps1",
    "scripts\patch_paper_trades_path.py",
    "scripts\apply_remove_paper_csv.ps1",
    "scripts\remove_paper_trades_writes.py",
    "scripts\find_paper_trades_refs.ps1",
    "scripts\cleanup_paper_trades.ps1"
)
foreach ($f in $junk) {
    if (Test-Path $f) { Remove-Item -Force $f; Write-Host ">>> Removed $f" }
}

Write-Host ">>> Cleanup complete."
