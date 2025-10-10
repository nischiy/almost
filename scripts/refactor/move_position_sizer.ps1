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

$ROOT   = (Resolve-Path -LiteralPath $ProjectRoot).Path
$src    = Join-Path $ROOT "utils\position_sizer.py"
$dstDir = Join-Path $ROOT "core\positions"
$dst    = Join-Path $dstDir "position_sizer.py"

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
  $tpl = Join-Path $ROOT "core\positions\position_sizer.py.tpl"
  if (Test-Path $tpl) {
    if ($WhatIf) { Write-Host "[WhatIf] SEED $dst from template" }
    else { Copy-Item -LiteralPath $tpl -Destination $dst -Force; Write-Host "[SEED] $dst" }
  } else {
    throw "Neither source nor destination module exists; aborting."
  }
}

# Patch imports: utils.position_sizer -> core.positions.position_sizer
$pyFiles = Get-ChildItem -Path $ROOT -Recurse -Filter "*.py" | Where-Object { $_.FullName -notmatch "\\.venv\\|\\tests\\\\" }
foreach ($f in $pyFiles) {
  $t = Get-Content -LiteralPath $f.FullName -Raw
  $n = $t
  $n = $n -replace "(?m)^\s*from\s+utils\.position_sizer\s+import\s+", "from core.positions.position_sizer import "
  $n = $n -replace "(?m)^\s*import\s+utils\.position_sizer\s+as\s+", "import core.positions.position_sizer as "
  $n = $n -replace "(?m)^\s*import\s+utils\.position_sizer\b", "import core.positions.position_sizer"
  $n = $n -replace "\butils\.position_sizer\b", "core.positions.position_sizer"
  if ($n -ne $t) {
    if ($WhatIf) { Write-Host "[WhatIf] PATCH $($f.FullName)" }
    else { Set-Content -LiteralPath $f.FullName -Value $n -Encoding UTF8; Write-Host "[PATCH] $($f.FullName)" }
  }
}

# Try to remove utils dir if empty
$utilsDir = Join-Path $ROOT "utils"
try {
  $remaining = Get-ChildItem -Path $utilsDir -Force
  if ($remaining.Count -eq 0) {
    if ($WhatIf) { Write-Host "[WhatIf] RMDIR $utilsDir" }
    else { Remove-Item -LiteralPath $utilsDir -Force; Write-Host "[RMDIR] $utilsDir" }
  }
} catch {}

Write-Host "[DONE] position_sizer moved to core.positions and imports patched."
