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
$src    = Join-Path $ROOT "utils\order_adapter.py"
$dstDir = Join-Path $ROOT "app\services"
$dst    = Join-Path $dstDir "order_adapter.py"

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
  $tpl = Join-Path $ROOT "app\services\order_adapter.py.tpl"
  if (Test-Path $tpl) {
    if ($WhatIf) { Write-Host "[WhatIf] SEED $dst from template" }
    else { Copy-Item -LiteralPath $tpl -Destination $dst -Force; Write-Host "[SEED] $dst" }
  } else {
    throw "Neither source nor destination module exists; aborting."
  }
}

# Patch imports across repo: utils.order_adapter -> app.services.order_adapter
$pyFiles = Get-ChildItem -Path $ROOT -Recurse -Filter "*.py" | Where-Object { $_.FullName -notmatch "\\.venv\\|\\tests\\\\" }
foreach ($f in $pyFiles) {
  $t = Get-Content -LiteralPath $f.FullName -Raw
  $n = $t
  # from utils.order_adapter import X -> from app.services.order_adapter import X
  $n = $n -replace "(?m)^\s*from\s+utils\.order_adapter\s+import\s+", "from app.services.order_adapter import "
  # import utils.order_adapter as oa -> import app.services.order_adapter as oa
  $n = $n -replace "(?m)^\s*import\s+utils\.order_adapter\s+as\s+", "import app.services.order_adapter as "
  # import utils.order_adapter -> import app.services.order_adapter
  $n = $n -replace "(?m)^\s*import\s+utils\.order_adapter\b", "import app.services.order_adapter"
  # usages utils.order_adapter.Foo -> app.services.order_adapter.Foo
  $n = $n -replace "\butils\.order_adapter\b", "app.services.order_adapter"
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

Write-Host "[DONE] order_adapter moved to app.services and imports patched."
