param(
  [string]$ProjectRoot = "."
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$dec = Join-Path -Path $root -ChildPath "logs\decisions"
New-Item -ItemType Directory -Path $dec -Force | Out-Null
$poke = Join-Path -Path $dec -ChildPath "poke.txt"
(Get-Date).ToString("s") | Out-File -LiteralPath $poke -Encoding UTF8 -Force
Write-Host "Poked decisions at $poke"
