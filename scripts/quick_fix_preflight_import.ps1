param([string]$ProjectRoot = ".")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$pf = Join-Path $root "tools\preflight\preflight_all.py"
if (-not (Test-Path -LiteralPath $pf)) { throw "preflight_all.py not found at $pf" }

$src = Get-Content -LiteralPath $pf -Raw

# Pattern we mistakenly inserted (contains literal \n)
$bad = 'from\s+core\.env_loader\s+import\s+load_env_files\s+as\s+load_env_file\\nfrom\s+tools\.common\.env_utils\s+import\s+to_bool,\s*require_keys,\s*write_json,\s*now_iso'

if ($src -match $bad) {
  $src = [regex]::Replace(
    $src,
    $bad,
    "from core.env_loader import load_env_files as load_env_file`r`nfrom tools.common.env_utils import to_bool, require_keys, write_json, now_iso"
  )
  Set-Content -LiteralPath $pf -Value $src -Encoding UTF8 -NoNewline:$false
  Write-Host "Fixed preflight_all.py import (inserted real newline)."
} else {
  Write-Host "No broken pattern found. Nothing to change."
}
