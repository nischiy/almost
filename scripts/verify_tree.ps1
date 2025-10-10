param([string]$Path = ".")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $Path).Path
Write-Host "=== Tree of $root ==="
Get-ChildItem -LiteralPath $root -Recurse | ForEach-Object {
  $rel = $_.FullName.Substring($root.Length).TrimStart('\')
  if ($rel) { Write-Host $rel }
}
