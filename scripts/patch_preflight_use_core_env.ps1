
param([string]$ProjectRoot = ".")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$pf = Join-Path $root "tools\preflight\preflight_all.py"
if (-not (Test-Path -LiteralPath $pf)) { throw "preflight_all.py not found at $pf" }

# Backup once
if (-not (Test-Path -LiteralPath ($pf + ".bak"))) {
  Copy-Item -LiteralPath $pf -Destination ($pf + ".bak") -Force
}

$src = Get-Content -LiteralPath $pf -Raw

# 1) Replace import of tools.common.env_utils.load_env_file with core.env_loader.load_env_files
$src = [regex]::Replace(
  $src,
  'from\s+tools\.common\.env_utils\s+import\s+load_env_file,\s*to_bool,\s*require_keys,\s*write_json,\s*now_iso',
  'from core.env_loader import load_env_files' + "`r`nfrom tools.common.env_utils import to_bool, require_keys, write_json, now_iso"
)

# 2) Replace the call site: load_env_file(env_path) -> load_env_files()
$src = $src -replace 'load_env_file\s*\(\s*env_path\s*\)', 'load_env_files()'

Set-Content -LiteralPath $pf -Value $src -Encoding UTF8 -NoNewline:$false
Write-Host "OK: preflight_all.py now uses core.env_loader.load_env_files()"
