# scripts\clean_duplicates.ps1
# Run this AFTER tests pass (python -m tests.self_check)
$ErrorActionPreference = "Stop"

$pathsToDelete = @(
  "core\strategies.py",   # duplicate of strategies package (remove after tests ok)
  "_previews"             # drafts
)

foreach ($p in $pathsToDelete) {
  if (Test-Path $p) {
    Write-Host "Removing $p ..."
    Remove-Item -Recurse -Force $p
  } else {
    Write-Host "Skip (not found): $p"
  }
}
Write-Host "Done. Consider removing extra README_* step files if not needed."
