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
$src    = Join-Path $ROOT "utils\sender_adapter.py"
$dstDir = Join-Path $ROOT "app\services"
$dst    = Join-Path $dstDir "notifications.py"

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
  $tpl = Join-Path $ROOT "app\services\notifications.py.tpl"
  if (Test-Path $tpl) {
    if ($WhatIf) { Write-Host "[WhatIf] SEED $dst from template" }
    else { Copy-Item -LiteralPath $tpl -Destination $dst -Force; Write-Host "[SEED] $dst" }
  } else {
    throw "Neither source nor destination module exists; aborting."
  }
}

# Patch imports across repo:
#  - utils.sender_adapter -> app.services.notifications
#  - (also normalize any app.services.sender_adapter -> app.services.notifications)
$pyFiles = Get-ChildItem -Path $ROOT -Recurse -Filter "*.py" | Where-Object { $_.FullName -notmatch "\\.venv\\|\\tests\\\\" }
foreach ($f in $pyFiles) {
  $t = Get-Content -LiteralPath $f.FullName -Raw
  $n = $t
  # from utils.sender_adapter import X -> from app.services.notifications import X
  $n = $n -replace "(?m)^\s*from\s+utils\.sender_adapter\s+import\s+", "from app.services.notifications import "
  # import utils.sender_adapter as alias -> import app.services.notifications as alias
  $n = $n -replace "(?m)^\s*import\s+utils\.sender_adapter\s+as\s+", "import app.services.notifications as "
  # import utils.sender_adapter -> import app.services.notifications
  $n = $n -replace "(?m)^\s*import\s+utils\.sender_adapter\b", "import app.services.notifications"
  # usages utils.sender_adapter.Foo -> app.services.notifications.Foo
  $n = $n -replace "\butils\.sender_adapter\b", "app.services.notifications"

  # Normalize any existing app.services.sender_adapter -> app.services.notifications
  $n = $n -replace "(?m)^\s*from\s+app\.services\.sender_adapter\s+import\s+", "from app.services.notifications import "
  $n = $n -replace "(?m)^\s*import\s+app\.services\.sender_adapter\s+as\s+", "import app.services.notifications as "
  $n = $n -replace "(?m)^\s*import\s+app\.services\.sender_adapter\b", "import app.services.notifications"
  $n = $n -replace "\bapp\.services\.sender_adapter\b", "app.services.notifications"

  if ($n -ne $t) {
    if ($WhatIf) { Write-Host "[WhatIf] PATCH $($f.FullName)" }
    else { Set-Content -LiteralPath $f.FullName -Value $n -Encoding UTF8; Write-Host "[PATCH] $($f.FullName)" }
  }
}

Write-Host "[DONE] sender_adapter relocated to app.services.notifications and imports patched."
