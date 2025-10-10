
param([string]$ProjectRoot = ".")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path

Write-Host "=== Scan for existing .env parsers ==="
Write-Host "ProjectRoot = $root"

$patterns = @(
  "load_dotenv",
  "dotenv_values",
  "from\s+dotenv\s+import",
  "decouple",
  "BaseSettings",          # pydantic settings
  "from\s+pydantic_settings\s+import",
  "class\s+\w+\(BaseSettings\)",
  "def\s+load_env",
  "def\s+get_env",
  "RISK_MAX_TRADES_PER_DAY", # direct key usage
  "os\.getenv\(",
  "ENV\s*=",
  "read_text\(\).*\.env"
)

$files = Get-ChildItem -LiteralPath $root -Recurse -Include *.py,*.ps1,*.psm1 -ErrorAction SilentlyContinue
$hits = @()

foreach ($f in $files) {
  $content = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue
  if ($null -eq $content) { continue }
  $score = 0
  foreach ($p in $patterns) {
    if ($content -match $p) { $score += 1 }
  }
  if ($score -gt 0) {
    $hits += [PSCustomObject]@{
      Path = $f.FullName
      Score = $score
    }
  }
}

$hits = $hits | Sort-Object -Property Score -Descending
if ($hits.Count -eq 0) {
  Write-Host "No obvious env parser found. (You can still use tools/common/env_utils.py)"
  exit 0
}

Write-Host "Top candidates:"
$hits | Select-Object -First 15 | ForEach-Object {
  "{0,3}  {1}" -f $_.Score, $_.Path
}

# Also dump machine-readable JSON (path + score)
$today = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
$outDir = Join-Path $root ("logs\preflight\{0}" -f $today)
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outPath = Join-Path $outDir "env_parser_candidates.json"
$hits | ConvertTo-Json | Set-Content -LiteralPath $outPath -Encoding UTF8 -NoNewline:$false
Write-Host "Saved JSON -> $outPath"
