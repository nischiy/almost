param(
  [string]$ProjectRoot = ".",
  [switch]$WhatIf
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Backup-File($path) {
  if (!(Test-Path $path)) { return }
  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  Copy-Item -LiteralPath $path -Destination ($path + ".bak.$stamp") -Force
}

$ROOT = (Resolve-Path -LiteralPath $ProjectRoot).Path
$src = Join-Path $ROOT "utils\live_bridge.py"
$dstDir = Join-Path $ROOT "app\services"
$dst = Join-Path $dstDir "bridge.py"

Write-Host ">>> ProjectRoot = $ROOT"
Write-Host ">>> Source: $src"
Write-Host ">>> Dest  : $dst"

if (!(Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir | Out-Null }

if (Test-Path $src) {
  if ($WhatIf) {
    Write-Host "[WhatIf] MOVE $src -> $dst"
  } else {
    if (Test-Path $dst) { Backup-File $dst }
    Move-Item -LiteralPath $src -Destination $dst -Force
    Write-Host "[MOVE] $src -> $dst"
  }
} elseif (!(Test-Path $dst)) {
  $tpl = Join-Path $ROOT "app\services\bridge.py.tpl"
  if (Test-Path $tpl) {
    if ($WhatIf) { Write-Host "[WhatIf] SEED $dst from template" }
    else { Copy-Item -LiteralPath $tpl -Destination $dst -Force; Write-Host "[SEED] $dst" }
  } else {
    throw "Neither source nor destination module exists; aborting."
  }
}

# Patch imports across repo:
# utils.live_bridge -> app.services.bridge
$pyFiles = Get-ChildItem -Path $ROOT -Recurse -Filter "*.py" | Where-Object { $_.FullName -notmatch "\\.venv\\|\\tests\\\\" }
foreach ($f in $pyFiles) {
  $t = Get-Content -LiteralPath $f.FullName -Raw
  $n = $t
  $n = $n -replace "(?m)^\s*from\s+utils\.live_bridge\s+import\s+", "from app.services.bridge import "
  $n = $n -replace "(?m)^\s*import\s+utils\.live_bridge\s+as\s+", "import app.services.bridge as "
  $n = $n -replace "(?m)^\s*import\s+utils\.live_bridge\b", "import app.services.bridge"
  $n = $n -replace "\butils\.live_bridge\b", "app.services.bridge"
  if ($n -ne $t) {
    if ($WhatIf) { Write-Host "[WhatIf] PATCH $($f.FullName)" }
    else { Set-Content -LiteralPath $f.FullName -Value $n -Encoding UTF8; Write-Host "[PATCH] $($f.FullName)" }
  }
}

# Clean empty utils dir if became empty
$utilsDir = Join-Path $ROOT "utils"
try {
  $left = Get-ChildItem -Path $utilsDir -Force | Where-Object { $_.PSIsContainer -or $_.Name -ne "" }
  if ($left.Count -eq 0) {
    if ($WhatIf) { Write-Host "[WhatIf] RMDIR $utilsDir" }
    else { Remove-Item -LiteralPath $utilsDir -Force; Write-Host "[RMDIR] $utilsDir" }
  }
} catch {}

Write-Host "[DONE] live_bridge moved to app.services.bridge and imports patched."
