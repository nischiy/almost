param(
  [string]$ProjectRoot = ".",
  [switch]$Aggressive  # if set, will attempt copy+truncate+delete
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$healthRoot = Join-Path -Path $root -ChildPath "logs\health"
$guardDir   = Join-Path -Path $healthRoot -ChildPath "guard"
if (-not (Test-Path -LiteralPath $healthRoot)) { return }
New-Item -ItemType Directory -Path $guardDir -Force | Out-Null

# target file list we want OUT of the health root
$targetNames = @(
  "health_loop.log",
  "health_loop.stdout.log",
  "health_loop.stderr.log",
  "heartbeat.json",
  "kill_switch.log",
  "kill_switch.stdout.log",
  "kill_switch.stderr.log"
)

# helper: try several strategies
function Move-Relaxed([string]$src, [string]$dst) {
  try {
    Move-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop
    return $true
  } catch {
    Start-Sleep -Milliseconds 150
    try {
      Move-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop
      return $true
    } catch {
      if ($Aggressive.IsPresent) {
        try {
          Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop
          # Truncate original
          $fs = [System.IO.File]::Open($src, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
          $fs.SetLength(0); $fs.Flush(); $fs.Close()
          # Remove best-effort
          Remove-Item -LiteralPath $src -Force -ErrorAction SilentlyContinue
          return $true
        } catch {
          return $false
        }
      }
      return $false
    }
  }
}

# pass 1: generic *.log/json/jsonl
Get-ChildItem -LiteralPath $healthRoot -File -ErrorAction SilentlyContinue | Where-Object {
  $_.Name -match '\.(log|json|jsonl)$'
} | ForEach-Object {
  $dst = Join-Path -Path $guardDir -ChildPath $_.Name
  [void](Move-Relaxed -src $_.FullName -dst $dst)
}

# pass 2: explicit names (just in case)
foreach ($name in $targetNames) {
  $src = Join-Path -Path $healthRoot -ChildPath $name
  if (Test-Path -LiteralPath $src) {
    $dst = Join-Path -Path $guardDir -ChildPath $name
    $ok = Move-Relaxed -src $src -dst $dst
    if (-not $ok) { Write-Warning "Could not relocate $name (locked?)" }
  }
}
