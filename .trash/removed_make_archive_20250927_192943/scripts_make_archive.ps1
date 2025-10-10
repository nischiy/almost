# make_archive.ps1
# Створює <ProjectName>_<Version>.zip без .venv, .idea, __pycache__, .git, .pytest_cache, logs
# Генерує .env.example (санітизований) і НЕ кладе .env у архів.
# Версію бере у такому порядку: параметр -Version -> файл VERSION -> pyproject.toml -> git tag -> дата.

param(
  [string]$Version
)

# 1) Визначаємо корінь проєкту (де лежить цей скрипт) і назву проєкту (назва теки)
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
$ProjectName = Split-Path -Leaf $ProjectRoot

function Get-Version {
  param([string]$ProjectRoot, [string]$VersionParam)

  if ($VersionParam -and $VersionParam.Trim().Length -gt 0) {
    return $VersionParam.Trim()
  }

  $verFile = Join-Path $ProjectRoot "VERSION"
  if (Test-Path $verFile) {
    $v = (Get-Content $verFile -Raw).Trim()
    if ($v) { return $v }
  }

  $pyproj = Join-Path $ProjectRoot "pyproject.toml"
  if (Test-Path $pyproj) {
    $raw = Get-Content $pyproj -Raw
    $m = [regex]::Match($raw, '(?m)^\s*version\s*=\s*"([^"]+)"\s*$')
    if ($m.Success) { return $m.Groups[1].Value.Trim() }
  }

  # git tag (опційно)
  $gitExe = (Get-Command git -ErrorAction SilentlyContinue)
  if ($gitExe) {
    $tag = git -C $ProjectRoot describe --tags --abbrev=0 2>$null
    if ($LASTEXITCODE -eq 0 -and $tag) { return $tag.Trim() }
  }

  # Фолбек — timestamp
  return (Get-Date -Format 'yyyyMMdd_HHmmss')
}

$ResolvedVersion = Get-Version -ProjectRoot $ProjectRoot -VersionParam $Version
$ZipName = "{0}_{1}.zip" -f $ProjectName, $ResolvedVersion

# 2) Шляхи
$OutDir  = Split-Path -Parent $ProjectRoot
$TempDir = Join-Path $OutDir  ("{0}_pkg_tmp" -f $ProjectName)
$ZipPath = Join-Path $OutDir  $ZipName

Write-Host ">>> Project: $ProjectName"
Write-Host ">>> Version: $ResolvedVersion"
Write-Host ">>> Output : $ZipPath" -ForegroundColor Cyan

Write-Host ">>> Cleaning temp dir..."
if (Test-Path $TempDir) { Remove-Item -Recurse -Force $TempDir }

# 3) Копіюємо проєкт у temp, виключивши службові/важкі теки
Write-Host ">>> Copying project to temp (excluding .venv/.idea/__pycache__/.git/.pytest_cache/logs)..."
robocopy $ProjectRoot $TempDir /MIR /XD .venv .idea __pycache__ .git .pytest_cache logs | Out-Null

# 4) Санітизація: .env -> .env.example, .env видаляємо
$EnvSrc = Join-Path $TempDir ".env"
$EnvExample = Join-Path $TempDir ".env.example"
if (Test-Path $EnvSrc) {
  $content = Get-Content $EnvSrc -Raw
  $sanitized = $content `
    -replace "(?m)^\s*BINANCE_API_KEY\s*=\s*.*$", "BINANCE_API_KEY=" `
    -replace "(?m)^\s*BINANCE_API_SECRET\s*=\s*.*$", "BINANCE_API_SECRET=" `
    -replace "(?m)^\s*BINANCE_TESTNET\s*=\s*.*$", "BINANCE_TESTNET=false" `
    -replace "(?m)^\s*TRADE_ENABLED\s*=\s*.*$", "TRADE_ENABLED=0" `
    -replace "(?m)^\s*PAPER_TRADING\s*=\s*.*$", "PAPER_TRADING=1"
  Set-Content -Path $EnvExample -Value $sanitized -Encoding UTF8
  Remove-Item $EnvSrc -Force
}

# 5) Перевірка кількості файлів перед пакуванням
$files = Get-ChildItem $TempDir -Recurse | Where-Object { -not $_.PSIsContainer }
Write-Host (">>> Files to zip: " + $files.Count)

# 6) Створюємо ZIP
Write-Host ">>> Creating zip..."
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipPath -Force

# 7) Прибирання
Write-Host ">>> Removing temp dir..."
Remove-Item -Recurse -Force $TempDir

Write-Host ">>> Archive ready: $ZipPath" -ForegroundColor Green
