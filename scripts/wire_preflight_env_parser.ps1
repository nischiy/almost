param(
  [string]$ProjectRoot = ".",
  [string]$ImportPath,
  [string]$FunctionName = "load_env"
)
$ErrorActionPreference = "Stop"
if (-not $ImportPath) { throw "Specify -ImportPath (e.g. myproj.config.env_loader)" }

$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$preflight = Join-Path $root "tools\preflight\preflight_all.py"
if (-not (Test-Path -LiteralPath $preflight)) {
  throw "preflight_all.py not found at $preflight"
}

# Backup
Copy-Item -LiteralPath $preflight -Destination ($preflight + ".bak") -Force

# Read source
$src = Get-Content -LiteralPath $preflight -Raw

# Compose replacement with a real newline between two imports
$replacement = ("from {0} import {1} as load_env_file`r`nfrom tools.common.env_utils import to_bool, require_keys, write_json, now_iso" -f $ImportPath, $FunctionName)

# Replace the original tools.common.env_utils import line
$src = [regex]::Replace(
  $src,
  'from\s+tools\.common\.env_utils\s+import\s+load_env_file,\s*to_bool,\s*require_keys,\s*write_json,\s*now_iso',
  $replacement
)

Set-Content -LiteralPath $preflight -Value $src -Encoding UTF8 -NoNewline:$false
Write-Host "preflight_all.py is now wired to use $ImportPath.$FunctionName() (newline-safe)"
