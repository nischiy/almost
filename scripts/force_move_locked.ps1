param(
  [string]$ProjectRoot = ".",
  [string[]]$Names = @(),
  [switch]$All
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$healthRoot = Join-Path -Path $root -ChildPath "logs\health"
$guardDir   = Join-Path -Path $healthRoot -ChildPath "guard"
New-Item -ItemType Directory -Path $guardDir -Force | Out-Null

function CopyAndTruncate([string]$src, [string]$dst){
  try { Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction SilentlyContinue } catch {}
  try {
    $fs = [System.IO.File]::Open($src, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    $fs.SetLength(0); $fs.Flush(); $fs.Close()
  } catch {}
  try { Remove-Item -LiteralPath $src -Force -ErrorAction SilentlyContinue } catch {}
}

# Build worklist
$work = New-Object System.Collections.Generic.List[string]
if ($All.IsPresent) {
  Get-ChildItem -LiteralPath $healthRoot -File -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match '\.(log|json|jsonl)$'
  } | ForEach-Object { $work.Add($_.FullName) }
}
foreach ($n in $Names) {
  $p = Join-Path -Path $healthRoot -ChildPath $n
  if (Test-Path -LiteralPath $p) { $work.Add($p) }
}

# Process
foreach ($src in $work) {
  $dst = Join-Path -Path $guardDir -ChildPath ([IO.Path]::GetFileName($src))
  try {
    Move-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop
    Write-Host ("Moved -> {0}" -f $dst)
  } catch {
    Write-Host ("Locked -> copy+truncate -> {0}" -f ([IO.Path]::GetFileName($src)))
    CopyAndTruncate -src $src -dst $dst
  }
}
