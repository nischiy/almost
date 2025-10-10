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
$src    = Join-Path $ROOT "utils\signer.py"
$dstDir = Join-Path $ROOT "core\execution"
$dst    = Join-Path $dstDir "signer.py"

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
  $tpl = Join-Path $ROOT "core\execution\signer.py.tpl"
  if (Test-Path $tpl) {
    if ($WhatIf) { Write-Host "[WhatIf] SEED $dst from template" }
    else { Copy-Item -LiteralPath $tpl -Destination $dst -Force; Write-Host "[SEED] $dst" }
  } else {
    throw "Neither source nor destination module exists; aborting."
  }
}

# Patch imports across repo: utils.signer -> core.execution.signer
$pyFiles = Get-ChildItem -Path $ROOT -Recurse -Filter "*.py" | Where-Object { $_.FullName -notmatch "\\.venv\\|\\tests\\\\" }
foreach ($f in $pyFiles) {
  $t = Get-Content -LiteralPath $f.FullName -Raw
  $n = $t
  $n = $n -replace "(?m)^\s*from\s+utils\.signer\s+import\s+", "from core.execution.signer import "
  $n = $n -replace "(?m)^\s*import\s+utils\.signer\s+as\s+", "import core.execution.signer as "
  $n = $n -replace "(?m)^\s*import\s+utils\.signer\b", "import core.execution.signer"
  $n = $n -replace "\butils\.signer\b", "core.execution.signer"
  if ($n -ne $t) {
    if ($WhatIf) { Write-Host "[WhatIf] PATCH $($f.FullName)" }
    else { Set-Content -LiteralPath $f.FullName -Value $n -Encoding UTF8; Write-Host "[PATCH] $($f.FullName)" }
  }
}

Write-Host "[DONE] signer moved to core.execution and imports patched.]"
